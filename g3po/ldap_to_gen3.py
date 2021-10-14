import os
import tempfile
from shutil import copyfile
from typing import Optional, List

import yaml
from ldap3 import (
    Server,
    Connection,
    SAFE_SYNC,
    ObjectDef,
    Reader,
)
from yglu.main import process


def generate_user_yaml(
    in_yaml_path: str,
    ldap_server: str,
    ldap_user: str,
    ldap_password: str,
    ldap_search_base: str,
) -> Optional[List[str]]:
    """
    Transforms a yglu YAML file using information from an LDAP server into a user.yaml for gen3.

    :param in_yaml_path: the input YAML path but with yglu annotations
    :param ldap_server: the server
    :param ldap_user: the LDAP user to bind
    :param ldap_password: the LDAP user password for bind
    :param ldap_search_base: the search base for the users we will output
    :return: an array of transform error messages if any, otherwise None
    """
    # because yglu is restricted to importing local files (only in same directory as in the input file) - we want to
    # make a temporary directory and do all our activity there - even if that means we need to do an extra
    # file copy of our input. Otherwise we would be littering the real file system with ldap.yaml files..

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        # get all the file paths we will need in our temp space
        tmp_input_path = os.path.join(tmp_dir_name, "user.in.yaml")
        tmp_output_path = os.path.join(tmp_dir_name, "user.yaml")
        tmp_ldap_path = os.path.join(tmp_dir_name, "ldap.yaml")

        # copy the specified input over into our working directory
        copyfile(in_yaml_path, tmp_input_path)

        # yglu kind of assumes all the files it is working on is in the current dir
        os.chdir(tmp_dir_name)

        server = Server(ldap_server)
        conn = Connection(
            server,
            ldap_user,
            ldap_password,
            client_strategy=SAFE_SYNC,
            auto_bind=True,
            read_only=True,
        )

        # An example search not using readers
        # status, result, response, _ = conn.search(
        #    search_base="ou=groups,o=UMCCR,o=CO,dc=biocommons,dc=org,dc=au",
        #    search_filter="(objectCategory=container)",
        #    search_scope=SUBTREE,
        #    attributes=ALL_ATTRIBUTES,
        # )

        obj_person = ObjectDef(["voPerson", "eduMember", "inetOrgPerson"], conn)

        r = Reader(conn, obj_person, ldap_search_base)

        # make a temporary YAML containing all our ldap entries - for inclusion into the yaml transform
        # (we could also make a groups yaml etc)
        ldap_data = []

        with open(tmp_ldap_path, "w") as ldap_out_file:
            for x in r.search():
                ldap_data.append(x.entry_attributes_as_dict)

            yaml.dump(ldap_data, ldap_out_file)

        errors = []

        with open(tmp_input_path) as in_file:
            with open(tmp_output_path, "w") as out_file:
                process(in_file, out_file, "user.in.yaml", errors)

                if errors:
                    return errors

        # output to stdout to make the CLI tool flexible
        with open(tmp_output_path, "r") as out_file:
            print(out_file.read())

        # return none to indicate there were no errors generated
        return None
