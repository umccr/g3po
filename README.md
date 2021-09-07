# g3po

Assorted utility CLI to work with Gen3

```
pip install g3po

g3po --help
g3po version
```

## Generate UUID

```
g3po uuid
g3po uuid --help
g3po uuid --count 10 | jq
```

## Data Dictionary Subcommand

You can convert/compile YAML schemas into a JSON as follows:

```
g3po dd convert local/yaml_schemas/ --out local/my_dd.json
```

e.g.
```
git clone https://github.com/umccr/umccr-dictionary.git
cd umccr-dictionary
g3po dd convert dictionary/umccr/ --out /tmp/umccr.json
g3po dd convert dictionary/gdc/ --out /tmp/gdc.json
g3po dd convert dictionary/anvil/ --out /tmp/anvil.json
```

## Index Subcommand
```
g3po index --help
g3po index health
g3po index stats
g3po index list
```

### Output Format

- You can pipe `jq` with `g3po` output for pretty JSON format
    ```
    g3po index list | jq
    ```

- Get index by GUID/DID
    ```
    g3po index get 1543974f-93e7-4f67-85ac-802e19ec11e8 | jq
    ```

### Env Var GEN3_URL

- You can override `GEN3_URL` environment variable to switch to different data commons
    ```
    GEN3_URL=https://caninedc.org/ g3po index list | jq
    ```

- Or, export `GEN3_URL` in your shell environment:
    ```
    export GEN3_URL=https://caninedc.org/
    g3po index get 0614e421-0cd6-4f93-ad1d-5f9354928bd2 | jq
    ```

- And unset the `GEN3_URL` env var:
    ```
    unset GEN3_URL
    ```

### Credentials

- Some sub-commands are required privilege access and, proper authz configured for performing index operations. e.g.

    ```
    g3po index delete --help
    Usage: g3po index delete [OPTIONS] GUID
    
    Options:
      --cred TEXT  Path to credentials.json i.e. API key from your profile
      --help       Show this message and exit.
    ```

- All sub-commands has optional `--cred` option. If this is not provided, it assumes to load from `~/.gen3/credentials.json` directory.

- Example, to delete by GUID/DID
    ```
    g3po index delete bd59f90a-286d-4688-96a6-777a6f1df79d
    ```

- Or, provide path to `credentials.json` file
    ```
    g3po index delete --cred /path/credentials.json bd59f90a-286d-4688-96a6-777a6f1df79d
    ```

### Creating Blank Index

- Help
    ```
    g3po index blank create --help
    Usage: g3po index blank create [OPTIONS]
    
    Options:
      --uploader TEXT  Uploading user within system, e.g. user.name@g3po.org
                       [required]
    
      --authz TEXT     Authz resources split by comma, e.g.
                       /programs/program1/projects/P1  [required]
    
      --filename TEXT  File name, e.g. test.bam
      --cred TEXT      Path to credentials.json downloaded from your profile
      --help           Show this message and exit.
    ```

- You can create a [blank index record](https://github.com/uc-cdis/indexd#blank-record-creation-in-indexd) as follows:
    ```
    g3po index blank create --uploader user.name@g3po.org --authz /programs/program1/projects/P1 | jq
    {
      "baseid": "93906e3e-6a1a-4e65-813b-dcec0763ae7b",
      "did": "835a367f-4f7d-4996-a562-e23f9d57cdeb",
      "rev": "6c75a7e8"
    }  
    ```
- Here, make sure `--uploader` option set to your login username for your Gen3 common site.
- And, also make sure `--authz` resource ACL has properly applied to your account in Fence `user.yaml` config.
- Blank index record has nothing yet. You can delete it back if you like so:
    ```
    g3po index delete 835a367f-4f7d-4996-a562-e23f9d57cdeb
    ```

### Updating Blank Index

- Help
    ```
    g3po index blank update --help
    Usage: g3po index blank update [OPTIONS]
    
    Options:
      --guid TEXT        Blank GUID/DID to update e.g.
                         1543974f-93e7-4f67-85ac-802e19ec11e8  [required]
    
      --rev TEXT         Current revision e.g. 7bd043f3  [required]
      --hash_type TEXT   Hash type e.g. md5  [required]
      --hash_value TEXT  Hash value e.g. ab167e49d25b488939b1ede42752458b
                         [required]
    
      --size INTEGER     File size in bytes, e.g. 1024  [required]
      --authz TEXT       Authz resources split by comma, e.g.
                         /programs/program1/projects/P1  [required]
    
      --urls TEXT        Resource URLs split by comma, e.g.
                         s3://bucket/1543974f-93e7-4f67-85ac-802e19ec11e8/test.txt
    
      --cred TEXT        Path to credentials.json downloaded from your profile
      --help             Show this message and exit.
    ```

- You can update a blank index record with hashes, size, etc... as follows:
    ```
    g3po index blank update \
      --guid bd59f90a-286d-4688-96a6-777a6f1df79d \
      --rev 5f8e7f9d \
      --hash_type md5 \
      --hash_value d0df0d078def0a5d7eb8ed6eb1e06099 \
      --size 7149868 \
      --urls s3://g3po-gen3-dev/bd59f90a-286d-4688-96a6-777a6f1df79d/somatic-PASS.vcf.gz \
      --authz /programs/program1/projects/P1 \
      | jq
    
    {
      "baseid": "811a7786-16ff-46d4-b9a2-1d647bdebfb9",
      "did": "bd59f90a-286d-4688-96a6-777a6f1df79d",
      "rev": "c203ed4d"
    }
    ```

## Manifest Indexing

- Help
    ```
    g3po index manifest --help
    Usage: g3po index manifest [OPTIONS]
    
    Options:
      --cred TEXT       Path to credentials.json downloaded from your profile
      --tsv TEXT        Path to manifest.tsv file
      --thread INTEGER  Number of thread, default 8
      --output TEXT     Output file
      --help            Show this message and exit.
    ```

- Download `credentials.json` API key from your profile. If `--cred` option is not specified, will look in `~/.gen3/credentials.json` directory.
- Download `manifest.tsv` [sample file](sample/manifest.tsv) and populate with data. If `--tsv` option is not specified, will look in current directory.
    ```
    tree .
    .
    └── manifest.tsv
    ```

**Generate Manifest Template:**
```
g3po index template
```

**Manifest Format:**
- `guid` - leave blank if you like Gen3 to generate GUID/DID.
    - Otherwise, generate UUID like so: `g3po uuid --count 10 | jq` or `uuid v4`
- `md5` - use [`md5sum`](https://en.wikipedia.org/wiki/Md5sum) to produce hashes for your file resource
- `size` - determine your file resource size in bytes. 
- `authz` - comma separated list of associated DD and resource authz ACL path that configured in Fence `user.yaml`.
- `file_name` - File name
- `urls` - comma separated list of the file resource URLs

**Validate Manifest Format:**
```
g3po index validate
validating "manifest.tsv" manifest
mapped manifest column "md5" to "MD5Validator" class instance
mapped manifest column "urls" to "URLValidator" class instance
mapped manifest column "size" to "SizeValidator" class instance
mapped manifest column "authz" to "AuthzValidator" class instance
finished validating "manifest.tsv" manifest, no errors were found
manifest.tsv is valid!
```

**Run:**
```
g3po index manifest

tree .
.
├── manifest.tsv
└── manifest_output_1601392690.tsv

less manifest_output_1601392690.tsv
```

## Development

- Activate virtual environment
- And install pip dependencies 
```
pip install -e '.[dev,tests]'
which g3po
g3po version
```
