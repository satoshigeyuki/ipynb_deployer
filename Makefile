PYTHONCMD     = python3.8
SOURCEDIR     = source
REPO_BASE     = reponame
REPO_WEBDIR   = docs
SPHINXDIR     = sphinx
TOCNAME       = $(shell env PYTHONPATH=$(SPHINXDIR) python3 -c 'import conf; print(conf.master_doc)')
PROJECT       = $(shell env PYTHONPATH=$(SPHINXDIR) python3 -c 'import conf; print(conf.project)')
DOCNAME       = $(shell env PYTHONPATH=$(SPHINXDIR) python3 -c 'import conf; print(conf.docname)')
GITHUB_USERNAME = $(shell env PYTHONPATH=$(SPHINXDIR) python3 -c 'import conf; print(conf.github_username)')
GITHUB_REPONAME = $(shell env PYTHONPATH=$(SPHINXDIR) python3 -c 'import conf; print(conf.github_reponame)')
GITHUB_BRANCH = $(shell env PYTHONPATH=$(SPHINXDIR) python3 -c 'import conf; print(conf.github_branch)')
COLAB_DIR     = $(shell env PYTHONPATH=$(SPHINXDIR) python3 -c 'import conf; print(conf.colab_dir)')
INDEX_NAME    = index_of_terms

all:
	@echo SOURCEDIR: $(SOURCEDIR)
	@echo REPO_BASE: $(REPO_BASE)
	@echo REPO_WEBDIR: $(REPO_WEBDIR)
	@echo SPHINXDIR: $(SPHINXDIR)
	@echo TOCNAME: $(TOCNAME)
	@echo PROJECT: $(PROJECT)
	@echo DOCNAME: $(DOCNAME)
	@echo GITHUB_USERNAME: $(GITHUB_USERNAME)
	@echo GITHUB_REPONAME: $(GITHUB_REPONAME)
	@echo GITHUB_BRANCH: $(GITHUB_BRANCH)
	@echo COLAB_DIR: $(COLAB_DIR)

index:
	-rm -fv $(SOURCEDIR)/$(INDEX_NAME).ipynb
	-mv -fv $(SOURCEDIR)/$(TOCNAME).ipynb $(SOURCEDIR)/$(TOCNAME).ipynb.stash
	$(PYTHONCMD) index_generator.py -s $(SOURCEDIR) -d $(SOURCEDIR) -n $(INDEX_NAME)
	-mv -fv $(SOURCEDIR)/$(TOCNAME).ipynb.stash $(SOURCEDIR)/$(TOCNAME).ipynb

toc:
	-rm -fv $(SOURCEDIR)/$(TOCNAME).ipynb
	$(PYTHONCMD) toc_generator.py -s $(SOURCEDIR) -n $(TOCNAME) -t "$(PROJECT)" -p toc_preamble.txt
	mv -v $(TOCNAME).ipynb $(SOURCEDIR)

sphinx: index toc
	cd $(SPHINXDIR); make SOURCEDIR=src clean
	$(PYTHONCMD) release.py -s $(SOURCEDIR) -x $(SPHINXDIR)/src
	rm -fv $(SPHINXDIR)/src/$(TOCNAME).ipynb
	cp -pv $(TOCNAME).rst $(SPHINXDIR)/src
	cd $(SPHINXDIR); make SOURCEDIR=src all

deploy:
	rm -fR $(REPO_BASE)/$(REPO_WEBDIR) $(REPO_BASE)/$(COLAB_DIR)
	cd $(SPHINXDIR); make REPODIR=$(abspath $(REPO_BASE)/$(REPO_WEBDIR)) deploy
	$(PYTHONCMD) release.py -s $(SOURCEDIR) -z $(REPO_BASE)/$(REPO_WEBDIR)/$(DOCNAME).zip
	$(PYTHONCMD) release.py -s $(SOURCEDIR) -r $(REPO_BASE) -g $(GITHUB_USERNAME) $(GITHUB_REPONAME) $(GITHUB_BRANCH) $(COLAB_DIR)

clean:
	-rm -fv $(SOURCEDIR)/$(TOCNAME).ipynb
	-rm -fv $(TOCNAME).rst
	-rm -fvr $(SPHINXDIR)/src

.PHONY: index toc sphinx deploy clean
