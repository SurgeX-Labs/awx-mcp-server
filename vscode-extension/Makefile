# Build and Package VS Code Extension

.PHONY: all install build package clean

all: install build package

install:
	npm install

build:
	npm run compile

package:
	npm run package

clean:
	rm -rf node_modules out *.vsix

test:
	npm test

watch:
	npm run watch
