UI_FILES:=$(wildcard ui/*.ui)
PY_FILES:=$(UI_FILES:%.ui=%.py)

all: ${PY_FILES}

ui/%.py: ui/%.ui
	pyside6-uic $^ -o $@
