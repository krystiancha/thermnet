all: black isort flake8

deploy:
	scp -r ./* ken.krystianch.com:.local/src/thermnet
	ssh ken.krystianch.com "chmod +x .local/src/thermnet/scripts/deploy && ~/.local/src/thermnet/scripts/deploy"

black:
	black thermnet

isort:
	isort --recursive thermnet

flake8:
	flake8 thermnet

pylint:
	pylint thermnet
