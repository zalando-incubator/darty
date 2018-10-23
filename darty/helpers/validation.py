from schema import Schema, Use


def validate_dependency_config(data):
    # TODO: move all validations for the config file here
    schema = Schema({
        'repositories': object,
        'dependencies': [{
            'version': Use(str),
            object: object,
        }],
    })

    return schema.validate(data)
