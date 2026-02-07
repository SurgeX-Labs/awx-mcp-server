"""Kubernetes task pod manager for AWX operations."""

import asyncio
import json
import os
from typing import Any, Dict, Optional

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False


class TaskPodManager:
    """Manages Kubernetes Job pods for AWX task execution."""
    
    def __init__(self, namespace: str = "default", image: str = "awx-mcp-server:latest"):
        """Initialize task pod manager."""
        self.namespace = namespace
        self.image = image
        self.enabled = KUBERNETES_AVAILABLE and os.environ.get("ENABLE_TASK_PODS", "false").lower() == "true"
        
        if self.enabled:
            try:
                # Try in-cluster config first
                config.load_incluster_config()
            except:
                # Fall back to kubeconfig
                config.load_kube_config()
            
            self.batch_v1 = client.BatchV1Api()
            self.core_v1 = client.CoreV1Api()
    
    async def execute_task(
        self,
        task_type: str,
        task_params: Dict[str, Any],
        tenant_id: str,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute AWX task in a Kubernetes Job pod.
        
        Args:
            task_type: Type of task (e.g., 'job_launch', 'list_templates')
            task_params: Parameters for the task
            tenant_id: Tenant ID for multi-tenancy
            timeout: Timeout in seconds
        
        Returns:
            Task execution result
        """
        if not self.enabled:
            raise RuntimeError("Task pods not enabled or Kubernetes client not available")
        
        job_name = f"awx-task-{task_type.replace('_', '-')}-{tenant_id[:8]}-{os.urandom(4).hex()}"
        
        # Create Job spec
        job = client.V1Job(
            apiVersion="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name,
                labels={
                    "app": "awx-mcp-task",
                    "task-type": task_type,
                    "tenant-id": tenant_id
                }
            ),
            spec=client.V1JobSpec(
                ttl_seconds_after_finished=300,
                backoff_limit=3,
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={
                            "app": "awx-mcp-task",
                            "task-type": task_type
                        }
                    ),
                    spec=client.V1PodSpec(
                        restart_policy="Never",
                        service_account_name="awx-mcp-server-task-runner",
                        containers=[
                            client.V1Container(
                                name="task",
                                image=self.image,
                                command=["python3", "/scripts/task-script.py"],
                                env=[
                                    client.V1EnvVar(name="TASK_TYPE", value=task_type),
                                    client.V1EnvVar(name="TASK_PARAMS", value=json.dumps(task_params)),
                                    client.V1EnvVar(name="TENANT_ID", value=tenant_id),
                                ],
                                volume_mounts=[
                                    client.V1VolumeMount(
                                        name="task-script",
                                        mount_path="/scripts"
                                    ),
                                    client.V1VolumeMount(
                                        name="data",
                                        mount_path="/home/awxmcp/.config/awx-mcp"
                                    )
                                ],
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": "100m", "memory": "128Mi"},
                                    limits={"cpu": "200m", "memory": "256Mi"}
                                )
                            )
                        ],
                        volumes=[
                            client.V1Volume(
                                name="task-script",
                                config_map=client.V1ConfigMapVolumeSource(
                                    name="awx-mcp-server-task-script",
                                    default_mode=0o755
                                )
                            ),
                            client.V1Volume(
                                name="data",
                                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                    claim_name="awx-mcp-server"
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        # Create the Job
        try:
            self.batch_v1.create_namespaced_job(namespace=self.namespace, body=job)
        except ApiException as e:
            raise RuntimeError(f"Failed to create task pod: {e}")
        
        # Wait for Job to complete
        result = await self._wait_for_job(job_name, timeout)
        
        # Clean up (Job TTL will handle automatic cleanup)
        # Optionally delete immediately: self.batch_v1.delete_namespaced_job(job_name, self.namespace)
        
        return result
    
    async def _wait_for_job(self, job_name: str, timeout: int) -> Dict[str, Any]:
        """Wait for Job to complete and get result from pod logs."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Task pod {job_name} timed out")
            
            # Get Job status
            try:
                job = self.batch_v1.read_namespaced_job(job_name, self.namespace)
            except ApiException:
                await asyncio.sleep(1)
                continue
            
            # Check if Job completed
            if job.status.succeeded:
                # Get pod logs
                pods = self.core_v1.list_namespaced_pod(
                    namespace=self.namespace,
                    label_selector=f"job-name={job_name}"
                )
                
                if pods.items:
                    pod_name = pods.items[0].metadata.name
                    try:
                        logs = self.core_v1.read_namespaced_pod_log(
                            name=pod_name,
                            namespace=self.namespace
                        )
                        # Parse JSON result from logs
                        return json.loads(logs)
                    except Exception as e:
                        return {"error": f"Failed to read pod logs: {e}"}
                
                return {"error": "No pods found for completed job"}
            
            elif job.status.failed:
                # Get pod logs for failure details
                pods = self.core_v1.list_namespaced_pod(
                    namespace=self.namespace,
                    label_selector=f"job-name={job_name}"
                )
                
                error_msg = "Task pod failed"
                if pods.items:
                    pod_name = pods.items[0].metadata.name
                    try:
                        logs = self.core_v1.read_namespaced_pod_log(
                            name=pod_name,
                            namespace=self.namespace
                        )
                        error_msg = f"Task pod failed: {logs}"
                    except:
                        pass
                
                return {"error": error_msg}
            
            # Job still running, wait a bit
            await asyncio.sleep(2)


# Global task pod manager instance
_task_pod_manager: Optional[TaskPodManager] = None


def get_task_pod_manager() -> Optional[TaskPodManager]:
    """Get global task pod manager instance."""
    global _task_pod_manager
    
    if _task_pod_manager is None and os.environ.get("ENABLE_TASK_PODS", "false").lower() == "true":
        namespace = os.environ.get("K8S_NAMESPACE", "default")
        image = os.environ.get("TASK_POD_IMAGE", "awx-mcp-server:latest")
        _task_pod_manager = TaskPodManager(namespace=namespace, image=image)
    
    return _task_pod_manager
