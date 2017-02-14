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
    ],

    entry_points={
        'console_scripts': '''


            mm-make-shots = mmpipeline.layout.makeshots:main
            mm-publish-art = mmpipeline.art.publish:main
            mm-publish-audio = mmpipeline.audio.publish:main

            # Deprecated (we prefer the "mm-" prefix).
            publish-art = mmpipeline.art.publish:main

        ''',
    },

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    
)
