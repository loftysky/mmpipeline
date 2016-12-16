from setuptools import setup, find_packages

setup(
    name='mmpipeline',
    version='0.1.dev0',
    description='Mark Media\'s general pipeline tools',
    url='http://github.com/mmpipeline/mmpipeline',
    
    packages=find_packages(exclude=['build*', 'tests*']),
    
    author='Mike Boers',
    author_email='mmpipeline@mikeboers.com',
    license='BSD-3',
    
    scripts=[
        'scripts/mm-fix-firefox',
        'scripts/mm-make-shots',
        'scripts/mm-publish-audio',
    ],

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    
)
