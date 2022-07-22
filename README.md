# osuAkatsuki's score service

## What is this?

The primary objective of this service is to serve as a nearly drag and drop replacement for Ripple's [LETS](https://github.com/osuripple/lets) as a score server. This means for existing server owners:
- Usage of the usual Ripple database schema.
- Full usage of the Ripple Redis API (pubsubs, keys etc).
- Full support of the Ripple JSON API.

All of this while also MASSIVELY improving upon LETS in the following areas:
- Massive performance gains
- Significantly more efficient with the database and other resources
- Modern asynchronous Python architecture
- Maintainable, modifiable codebase
