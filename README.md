# Darty

__Darty__ is a data dependency manager for data science projects. 
It helps to share data across projects and control data versions.

## Getting Started

### Installation

Requirements:
- Python 3
- Installed and configured [AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html)
- Bucket on S3 to publish your packages

Use [pip](http://www.pip-installer.org/en/latest/) to install or upgrade Darty:

```bash
$ pip install -U darty
```

### Dependency File

To manage data dependencies the project should contain a configuration file. By default
Darty is looking for a `darty.yaml` file.

Example of a dependency file:

```yaml
repositories:
  default:
    type: s3_zip
    root: sapphire-data-packages
    
dependencies:
  - group: entity_detection.lexicons
    artifact: lexicons-en
    version: 1.1.0
    workingDir: data/lexicons/en

  - group: entity_detection.lexicons
    artifact: lexicons-de
    version: 1.0.0
    workingDir: data/lexicons/de
```

The file contains a list of repositories and a list of dependencies. Each dependency belongs to particular repository.
By default all dependencies belong to the "default" repository.

__“repositories”__ section is a dictionary of repositories where keys are names of repositories and values are
configurations.

Repository configuration:
- __“type”__: name of the repository driver (see "[Darty Drivers](#darty-drivers)" section)
- __“root”__: unique identificator inside the repository. Meaning of this value is different for 
different types of repositories. For Amazon S3 it’s a bucket name.
- __“parameters”__: custom parameters for the repository driver.

__“dependencies”__ section is a list of elements where each element contains dependency configuration.

Dependency configuration:
- __“group”__: the id of the data group.
- __“artifact”__: the name of the package under the specified group.
- __“version”__: the version of the package under the specified group.
- __“working-dir”__ _(optional)_: this directory is being used to work with package files directly from the project 
and to publish the new version of the package.
- __“files”__ _(optional)_: list of files which belong to the package. It can be used to specify particular files 
which should be copied to the working directory ignoring other ones. Or it can be used to scope the list of files 
which you want to publish inside new version of the package.
- __“repository”__ _(optional)_: the name of the repository where the package is located (by default 
it has value "default", then the "default" repository must be specified)

##### Shared Working Directory

You can use the same working directory for several dependencies, but in this case 
you must use __“files”__ setting. You must specify the list of files for each dependency 
which you are going to use. The files across dependencies which are sharing 
the same working directory cannot have the same filenames.


### Publishing Data Package

1. Create a working directory for the data you want to publish. For example, `data/my_word_vectors/`.
2. Create the `darty.yaml` file in the project's root folder:
    ```yaml
    repositories:
      default:
        type: s3_zip                       # name of the driver for S3
        root: my-data-packages             # bucket name
        
    dependencies:
      - group: datasets.word_vectors       # package group name
        artifact: my-word-vectors          # package artifact name
        version: 1.0.0                     # package version
        workingDir: data/my_word_vectors   # package working directory
    ```

3. Make sure you've configured AWS CLI and have an access to the bucket.
4. Go to the project’s directory in the terminal and run the following command:
    ```bash
    $ darty publish
    ```
    
    If everything was configured correctly you will see the message that the package was successfully 
    published and the list of published files.


##### Local Publishing

Package can be published locally. Then it will be available for all your local projects.
Use the `publish-local` command. To rewrite existing version of local package, use __"-r"__ flag.

```bash
$ darty publish-local
```

### Downloading Dependencies

Tu get all the dependencies specified in the configuration file, use the following command:

```bash
$ darty update
```

__Note:__ if the working directory for the dependency is not empty, it __will not__ be updated.
To rewrite working directories for the dependencies, use __"-r"__ flag.

By default Darty is looking for a `darty.yaml` file in the current directory, but you can specify
the path to your dependency file using __"-c"__ flag:

```bash
$ darty update -c path/to/project/config.yaml
```

Also you can get only particular dependency from the list by specifying a group and an artifact name 
or just an artifact name:

```bash
$ darty update --group {{package_group}} --artifact {{package_artifact}}
$ darty update --artifact {{package_artifact}}
```


## Integration with a Python Project

Integration of Darty with your project would be helpful if:
- you want to distribute your Python package, and the data should be outside of this package
- you have a heavy dataset and you don't want to have the second copy in the dependency working directory
(the first copy Darty always caches in the `~/.darty` directory and it's for a read-only access)

Integration steps:

1. Move the `darty.yaml` file from the project root directory inside your Python package. Don’t forget to rewrite 
all relative paths for working directories inside the file.

2. Create an instance of __DependencyManager__ in the **{{package_name}}/\_\_init\_\_.py** file:

    ```python
    from darty.dependency_manager import DependencyManager
    DM = DependencyManager.from_py_package(__package__)
    ```

3. Use __get_path()__ method to get path to your data package:

    ```python
    from {{package_name}} import DM
    lexicons_path = DM.get_path('entity_detection.lexicons', 'lexicons-en', file_path='en-curated-color')
    ```

__Note:__ the __get_path()__ method is trying to find the files in the working directory if the directory exists. 
If it doesn't exist or it's empty, the method will return the absolute path to the data package.

Python package distribution:

1. Add the path to the `darty.yaml` file to the __setup.py__ script:

    ```python
    setup(name='{{package_name}}',
          ...
          package_data={'{{package_name}}': [
               'darty.yaml',
               ...
          ]})
    ```

2. Now if user installed your Python package with __pip__, he can get the data dependencies 
using the following command:

    ```bash
    $ darty download --py-package {{package_name}}
    ```

    Because you are using __"download"__ command and not __"update"__, the working directories
    for data dependencies **_will not_** be created, and the application will access files using 
    absolute paths.


## Darty Configuration

Darty keeps its configuration in the `~/.darty/config` file.

To change default settings use the following command:

```
$ darty [-p <PROFILE_NAME>] configure
```

If you didn't specify a configuration profile name, name __"default"__  will be used by default.

At the moment the command allows you to configure only the directory where data packages will be 
saved locally. By default, it's the directory `~/.darty/packages/`.


## Darty Drivers

At the moment Darty supports only AWS S3 buckets, but you can always develop your custom driver as a plugin to
Darty and use it in your dependency files.

This repository contains 2 S3 drivers:
- __s3_files__: stores packages on S3 as a bunch of files, without packing them to a single archive,
- __s3_zip__: stores packages on S3 as zip archives.


## FAQ

#### 1. Where all my downloaded and locally published packages are stored?

By default, all packages are stored in the `~/.darty/packages/` directory, but you can change
it using the `configure` command.

#### 2. What is "working directory"?

You can specify a working directory for any dependency in your dependency file. Once 
a package is downloaded to the local central directory, the data from that package will
be copied to the specified working directory. You should use working directories in 2 cases:
- if you want to work with the data using relative to your project's root paths
- if you are going to modify and publish a new version of the package

#### 3. How to work with package data if I didn't specify a working directory?

You can do it only if you're working with a Python project. See _"Integration 
with a Python Project"_ section.

#### 4. Can I specify the same working directory for several dependencies?

Yes, you can share a working directory across several packages. See 
_"Shared Working Directory"_ section.

#### 5. If I have changes in a dependency working directory and I call the update command, will I loose my changes?

No, you won't. All the files in the working directory will remain unchanged. Only if you 
called the command with the `-r` flag, they will be overwritten.

If you have a list of files for the dependency specified and you call update command,
the existing files in the working directory will remain unchanged, but those ones which
didn't exist in the directory before will be appended.

#### 6. How can I resolve the conflict if I've made some changes to the package, but another person just published newer version of this package?

Follow the steps:
1. Rename the current working directory for the package to something temporary.
2. Change the version of the package in the __darty.yaml__ file to the latest one.
3. Perform `darty update` command. It will download the latest package and 
create a new working directory with the latest data.
4. Move your changes to newly created directory and remove the temporary one.
5. Now you can publish a new version of the package.


## TODO

- add "author" (dict: "name", "email") field for dependency configuration
- wildcards for files in the dependency configuration
- "show" command similar to [pip show](https://pip.pypa.io/en/stable/reference/pip_show/)
- command to get package versions from repository (show -i 1 -f (to show also files), -v (to 
show also available versions in repository). Returns information about installed package (env 
flag, without files by default; or print "Not installed")
- "clean" command to remove locally published package
- "compare" command to compare current working directory with particular version of the package
- add "message" parameter for the "publish" command and save it to package metadata


## Contributing
Darty welcomes contributions from the open source community. To get started, take a look at our 
[contributing guidelines](CONTRIBUTING.md), then check the [Issues Tracker](https://github.com/zalando-incubator/darty/issues) for ideas.


## Contact
Feel free to contact one the [maintainers](MAINTAINERS).


## License
See the [LICENSE](LICENSE) file.
