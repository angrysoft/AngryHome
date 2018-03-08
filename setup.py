from distutils.core import setup
from glob import glob

confFile = glob('files/*.json')
wwwStatic = glob('src/static/*css') + glob('src/static/*.dart') + glob('src/static/*.dart.js')
wwwTemp = glob('src/templates/*.html')


setup(name='SmartHouse',
    version='0.4',
    description='House Automatization',
    url='https://bitbucket.org/angrysoft/Smarthouse',
    author='Sebastian Zwierzchowski',
    author_email='sebastian.zwierzchowski@gmail.com',
    license='GPL2',
    data_files=[('/etc/smarthouse', confFile),
                ('/var/www/smarthouse/static', wwwStatic),
                ('/var/www/smarthouse/templates', wwwTemp),
                ('/var/www/smarthouse', 'src/Smarthouse.py'),
                ('/usr/lib/systemd/system', 'housed.service')],
    scripts=['src/housed.py'],
    requires=["flask", "pyserial"]
    )
