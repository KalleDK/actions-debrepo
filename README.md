# Create DEB Repo

Used to generate and sign an DEB repository

```yaml
- name: Build DEB Repo
  uses: KalleDK/actions-debrepo@v0.0.1
  id: build_debrepo
  with:
    key_name: <keyname>
    key_priv: ${{ secrets.DEB_KEY_PRIV }}
    key_pub: ${{ vars.DEB_KEY_PUB }}
    repo_url: https://<username>.github.io/deb
    repo_name: <reponame>
    repo_pkgs: pkgs
```
