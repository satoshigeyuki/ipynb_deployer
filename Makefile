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

toc:
	-rm -fv $(SOURCEDIR)/$(TOCNAME).ipynb
	$(PYTHONCMD) toc_generator.py -s $(SOURCEDIR) -n $(TOCNAME) -t "$(PROJECT)" -p toc_preamble.txt
	mv -v $(TOCNAME).ipynb $(SOURCEDIR)

sphinx: toc
	-rm -fvr $(SPHINXDIR)/src
	$(PYTHONCMD) release.py -s $(SOURCEDIR) -x $(SPHINXDIR)/src
	rm -fv $(SPHINXDIR)/src/$(TOCNAME).ipynb
	cp -pv $(TOCNAME).rst $(SPHINXDIR)/src
	cd $(SPHINXDIR); make SOURCEDIR=src all

deploy:
	cd $(SPHINXDIR); make REPODIR=$(abspath $(REPO_BASE)/$(REPO_WEBDIR)) deploy
	$(PYTHONCMD) release.py -s $(SOURCEDIR) -z $(REPO_BASE)/$(REPO_WEBDIR)/$(DOCNAME).zip
	$(PYTHONCMD) release.py -s $(SOURCEDIR) -r $(REPO_BASE) -g $(GITHUB_USERNAME) $(GITHUB_REPONAME) $(GITHUB_BRANCH) $(COLAB_DIR)

clean:
	-rm -fv $(SOURCEDIR)/$(TOCNAME).ipynb
	-rm -fv $(TOCNAME).rst
	-rm -fvr $(SPHINXDIR)/src

.PHONY: toc sphinx deploy clean
