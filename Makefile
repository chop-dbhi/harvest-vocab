STATIC_DIR = vocab/static/vocab
COFFEE_DIR = ${STATIC_DIR}/scripts/coffeescript
JS_SRC_DIR = ${STATIC_DIR}/scripts/javascript/src
JS_MIN_DIR = ${STATIC_DIR}/scripts/javascript/min
PID_FILE = .watch-pid

SASS_DIR = ${STATIC_DIR}/stylesheets/scss
CSS_DIR = ${STATIC_DIR}/stylesheets/css

COMPILE_SASS = `which sass` --scss --style=compressed -r ${SASS_DIR}/bourbon/lib/bourbon.rb ${SASS_DIR}:${CSS_DIR}
COMPILE_COFFEE = `which coffee` -b -o ${JS_SRC_DIR} -c ${COFFEE_DIR}
WATCH_COFFEE = `which coffee` -w -b -o ${JS_SRC_DIR} -c ${COFFEE_DIR}
REQUIRE_OPTIMIZE = `which node` bin/r.js -o ${STATIC_DIR}/scripts/javascript/app.build.js

LATEST_TAG = `git describe --tags \`git rev-list --tags --max-count=1\``

all: build-submodules watch

build: clean build-submodules sass coffee optimize

dist: build
	@echo 'Creating a source distributions...'
	@python setup.py sdist > /dev/null

sass:
	@echo 'Compiling Sass...'
	@mkdir -p ${CSS_DIR}
	@${COMPILE_SASS} --update

coffee:
	@echo 'Compiling CoffeeScript...'
	@mkdir -p ${JS_SRC_DIR}
	@${COMPILE_COFFEE}

watch: unwatch
	@echo 'Watching in the background...'
	@mkdir -p ${CSS_DIR} ${JS_SRC_DIR}
	@${WATCH_COFFEE} &> /dev/null & echo $$! > ${PID_FILE}
	@${COMPILE_SASS} --watch &> /dev/null & echo $$! >> ${PID_FILE}

unwatch:
	@if [ -f ${PID_FILE} ]; then \
		echo 'Watchers stopped'; \
		for pid in `cat ${PID_FILE}`; do kill -9 $$pid; done; \
		rm ${PID_FILE}; \
	fi;

init-submodules:
	@echo 'Initializing submodules...'
	@if [ -d .git ]; then \
		if git submodule status | grep -q -E '^-'; then \
			git submodule update --init --recursive; \
		else \
			git submodule update --init --recursive --merge; \
		fi; \
	fi;

build-submodules: init-submodules rjs

rjs:
	@echo 'Setting up r.js...'
	@cd ./modules/r.js && node dist.js
	@mkdir -p ./bin
	@cp ./modules/r.js/r.js ./bin

optimize:
	@echo 'Optimizing the javascript...'
	@rm -rf ${JS_MIN_DIR}
	@mkdir -p ${JS_MIN_DIR}
	@${REQUIRE_OPTIMIZE} > /dev/null

clean:
	@rm -rf ${JS_SRC_DIR} ${JS_MIN_DIR} ${CSS_DIR}

.PHONY: all sass coffee watch unwatch build optimize clean
