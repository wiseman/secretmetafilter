WEB_DIR = modules/lib/mavelous_web
JS_SCRIPT_DIR = secretmefi/static
TOOL_DEPS_ROOT = .tools

CLOSURE_COMPILER_URL = http://closure-compiler.googlecode.com/files/compiler-latest.zip
CLOSURE_COMPILER_DIR = ${TOOL_DEPS_ROOT}/compiler
CLOSURE_COMPILER = ${CLOSURE_COMPILER_DIR}/compiler.jar

VIRTUALENV_DIR = ${TOOL_DEPS_ROOT}/env

CLOSURE_LIBRARY_URL = https://code.google.com/p/closure-library/
CLOSURE_LIBRARY_DIR = closure-library
CLOSURE_BUILDER = ${CLOSURE_LIBRARY_DIR}/closure/bin/build/closurebuilder.py

JS_FILES = app.js

JS_SRCS = $(addprefix ${JS_SCRIPT_DIR}/,${JS_FILES})

MAVELOUS_TARGETS = ${JS_SCRIPT_DIR}/app.min.js

.PHONY: all build lint lintfix clean build-tool-deps


all: build

build: build-tool-deps ${MAVELOUS_TARGETS}

deps: ${JS_SCRIPT_DIR}/mavelous-deps.js

lint:
	-gjslint --unix_mode --strict ${JS_SRCS}
	-jshint --config=jshintrc ${JS_SRCS}

lintfix:
	fixjsstyle --strict ${JS_SRCS}

clean:
	-rm ${MAVELOUS_TARGETS}


build-tool-deps: ${CLOSURE_COMPILER} ${CLOSURE_BUILDER}


${JS_SCRIPT_DIR}/app.min.js: ${JS_SRCS}
	python ${CLOSURE_BUILDER} \
	    --root=${CLOSURE_LIBRARY_DIR}/closure/goog \
	    --root=${CLOSURE_LIBRARY_DIR}/third_party/closure \
	    --root=${JS_SCRIPT_DIR} \
	    --namespace="SecretMefi.App" \
	    --output_mode=compiled \
	    --compiler_jar=${CLOSURE_COMPILER} \
	    --compiler_flags="--compilation_level=ADVANCED_OPTIMIZATIONS" \
	    --compiler_flags="--summary_detail_level=3" \
	    --compiler_flags="--warning_level=VERBOSE" \
	    --compiler_flags="--generate_exports" \
	    --compiler_flags="--js_output_file=$@"


${JS_SCRIPT_DIR}/mavelous-deps.js: ${JS_SRCS}
	python ${CLOSURE_LIBRARY_DIR}/closure/bin/calcdeps.py \
	 --dep=${CLOSURE_LIBRARY_DIR} \
	 --path=${JS_SCRIPT_DIR} \
	 --exclude=${JS_SCRIPT_DIR}/mavelous.min.js \
	 --output_mode=deps \
	| sort > $@


${WEB_DIR}/index.html: ${WEB_DIR}/index.tmpl
	python jinja_static.py ${WEB_DIR}/index.tmpl --output_file=${WEB_DIR}/index.html

${WEB_DIR}/index_compiled.html: ${WEB_DIR}/index.tmpl
	python jinja_static.py ${WEB_DIR}/index.tmpl -D compiled --output_file=${WEB_DIR}/index_compiled.html



${CLOSURE_COMPILER}:
	mkdir -p ${CLOSURE_COMPILER_DIR}
	(cd ${CLOSURE_COMPILER_DIR}; \
	 curl -O "${CLOSURE_COMPILER_URL}"; \
	 unzip compiler-latest.zip; \
	 rm compiler-latest.zip);

${CLOSURE_BUILDER}:
	git clone ${CLOSURE_LIBRARY_URL}
