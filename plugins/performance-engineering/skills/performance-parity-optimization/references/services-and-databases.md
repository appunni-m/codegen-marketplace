# Service and database performance patterns

Load this reference when the measured operation crosses query, network, queue,
serialization, cache, transaction, or downstream service boundaries.

- Inspect the actual query plan, estimated and observed row counts, indexes,
  round trips, lock waits, and bytes returned. Validate plan changes on
  representative data distributions and parameter values.
- Time queue wait, application work, serialization, network transfer, retries,
  and downstream calls separately. Attribute end-to-end latency to the critical
  path rather than summing parallel worker time.
- Measure write cost, skew, cache invalidation, transaction boundaries,
  connection-pool behavior, backpressure, and tail latency alongside fast-path
  read latency.
- Use an open offered-load model for a fixed incoming rate; use a closed
  workload when callers really wait for each prior request. Keep the load
  generator below saturation and record dropped work so client limits do not
  masquerade as server throughput.
- Test single-request latency and aggregate completed work at equivalent
  concurrency. Track queue growth, memory, failures, retries, and latency
  percentiles. A throughput gain that breaches latency or resource limits is
  not an accepted optimization.
