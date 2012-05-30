# Set the task name
TASK = dea

# Versions
VERSION = `python dea_check.py --version`

# Uncomment the correct choice indicating either SKA or TST flight environment
FLIGHT_ENV = SKA

BIN = dea_check
SHARE = dea_check.py VERSION dea_model_spec.json \
	index_template.rst index_template_val_only.rst dea_check.css html4css1.css
DATA = task_schedule.cfg

DOC = doc/_build/html

include /proj/sot/ska/include/Makefile.FLIGHT

.PHONY: dist install doc

# Make a versioned distribution.  Could also use an EXCLUDE_MANIFEST
dist: version
	mkdir $(TASK)-$(VER)
	tar --exclude CVS --exclude "*~" --create --files-from=MANIFEST --file - \
	 | (tar --extract --directory $(TASK)-$(VER) --file - )
	tar --create --verbose --gzip --file $(TASK)-$(VER).tar.gz $(TASK)-$(VER)
	rm -rf $(TASK)-$(VER)

doc:
	cd doc ; \
	make html

install: 
#  Uncomment the lines which apply for this task
	mkdir -p $(INSTALL_BIN)
	mkdir -p $(INSTALL_SHARE)
	mkdir -p $(INSTALL_DATA)
	mkdir -p $(INSTALL_DOC)

	rsync --times --cvs-exclude $(BIN) $(INSTALL_BIN)/
	rsync --times --cvs-exclude $(SHARE) $(INSTALL_SHARE)/
	rsync --times --cvs-exclude $(DATA) $(INSTALL_DATA)/
	rsync --recursive --links --times -D --cvs-exclude $(DOC)/ $(INSTALL_DOC)/

