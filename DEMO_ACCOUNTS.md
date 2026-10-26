# Disposable demo accounts

Run `seed_bookleaf_data` against the supplied JSON to create these demonstration accounts. They are not real user credentials.

- Admin: `admin@bookleaf.demo`
- Author example: `priya.sharma@email.com` (other supplied author emails also work)
- Initial password for newly created demo accounts: `BookleafDemo123!`

Passwords are hashed by Django. Re-running the seed command preserves changed passwords. Use a custom `--password` when first creating a disposable deployment, keep its value out of version control, and remove demo accounts before handling real author data.
