.PHONY: dist
install:
	@pip install -e '.[dev,tests]'

dist:
	@python setup.py sdist bdist_wheel

# Usage: make testpypi version=0.2.0
testpypi: dist/g3po-$(version).tar.gz
	@twine upload --repository testpypi --sign dist/g3po-$(version)*

pypi: dist/g3po-$(version).tar.gz
	@twine upload --sign dist/g3po-$(version)*

image:
	@docker build -t victorskl/g3po:latest .

push:
	@docker image tag victorskl/g3po:latest quay.io/victorskl/g3po:latest
	@docker image tag victorskl/g3po:latest quay.io/umccr/g3po:latest
	@docker push victorskl/g3po:latest
	@docker push quay.io/victorskl/g3po:latest
	@docker push quay.io/umccr/g3po:latest

# Usage: make tag version=0.5.0
tag:
	@docker image tag victorskl/g3po:latest quay.io/umccr/g3po:$(version)
	@docker image tag victorskl/g3po:latest quay.io/victorskl/g3po:$(version)
	@docker image tag victorskl/g3po:latest victorskl/g3po:$(version)
	@docker push quay.io/umccr/g3po:$(version)
	@docker push quay.io/victorskl/g3po:$(version)
	@docker push victorskl/g3po:$(version)
