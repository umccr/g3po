.PHONY: dist
dist:
	@python setup.py sdist bdist_wheel

# Usage: make testpypi version=0.2.0
testpypi: dist/g3po-$(version).tar.gz
	@twine upload --repository testpypi --sign dist/g3po-$(version)*

pypi: dist/g3po-$(version).tar.gz
	@twine upload --sign dist/g3po-$(version)*
