# SHIFT│DOSE™ Meta Product Feed

Automated Meta/Facebook product feed for **SHIFT│DOSE™**.

Source: public WooCommerce Store API at https://shiftdose.com

## Feed URL

`https://raw.githubusercontent.com/klayd83/shiftdose-meta-feed/main/feed.csv`

The feed is regenerated every 6 hours by GitHub Actions and can also be refreshed manually with the **Update Meta product feed** workflow.

### Catalog matching

The feed uses the exact WooCommerce product ID as the catalog `id`. PixelYourSite on shiftdose.com also sends WooCommerce product IDs in Meta `content_ids`, so browser events and catalog items can match for catalog/dynamic ads.

No credentials or customer data are stored in this repository.
