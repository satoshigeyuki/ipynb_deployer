SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = # to be specified in arguments of make
BUILDDIR      = build
DOCNAME       = $(shell python3 -c 'import conf; print(conf.docname)')
REPODIR       = # to be specified in arguments of make

all: html latex

html:
	-mkdir html
	-ln -s ../conf.py html/
	$(SPHINXBUILD) -M html -c . $(SOURCEDIR) $(BUILDDIR)/html

latex:
	-mkdir latex
	-ln -s ../conf.py latex/
	$(SPHINXBUILD) -M latex -c . $(SOURCEDIR) $(BUILDDIR)/latex
	python3 latex_sanitizer.py $(BUILDDIR)/latex/$(DOCNAME).tex
	cd $(BUILDDIR)/latex; platex -halt-on-error $(DOCNAME)
	cd $(BUILDDIR)/latex; platex -halt-on-error $(DOCNAME)
	cd $(BUILDDIR)/latex; dvipdfmx $(DOCNAME)

deploy:
	cp -vfprT $(BUILDDIR)/html $(REPODIR)
	rm -vfr $(REPODIR)/_sources
	find $(REPODIR) -name '*.ipynb' -delete -print
	cp -vpf $(BUILDDIR)/latex/$(DOCNAME).pdf $(REPODIR)

clean:
	-rm -fR $(BUILDDIR) doctrees $(SOURCEDIR) latex html

.PHONY: html latex deploy clean
