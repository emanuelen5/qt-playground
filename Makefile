UI_FILES:=$(find . -name *.ui)
PY_FILES:=$(UI_FILES:%.ui=%.py)

all: ui
ui: ${PY_FILES}

%.py: %.ui
	pyside6-uic $^ -o $@

.PHONY: all ui
