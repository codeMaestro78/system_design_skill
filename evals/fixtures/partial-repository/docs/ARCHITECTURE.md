# Target architecture

Planned split of this prototype into three services:

- `orders-api` - owns the `orders` table and publishes `order.created` to Kafka.
- `billing-service` - consumes order events and calls Stripe.
- `catalog-service` - owns products and serves the public read API from a read replica.

Kafka gives exactly-once delivery between the services, and the API gateway in front of
`orders-api` validates the JWT bearer token before forwarding a request.
