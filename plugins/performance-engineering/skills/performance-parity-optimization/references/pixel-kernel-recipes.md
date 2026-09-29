# Pixel-kernel recipes

Load this reference for image and tensor kernels with channelized, masked,
interleaved, or packed values. The examples illustrate reusable implementation
shapes. Confirm the active library's exact format rules, numeric order, and
fallback behavior before applying them.

## Same-layout copy and masked blend

- For an unmasked same-format paste, check whether the public wrapper already
  normalized the source. If source and destination layouts match, share the
  source, clone the destination in its existing concrete type only when
  mutation requires it, and copy clipped row spans. Keep masks on the blend
  path because coverage and per-channel rounding change the operation.
- For a masked raster operation, calculate clipping, source/destination/mask
  strides, and row spans outside the pixel loop. Read only the mask band used
  by the reference operation, but apply its coverage to every destination
  sample that the reference blends. Prove row bounds before using contiguous
  slices. Use a direct contiguous mask load for matching single-channel layouts
  only when profiling shows gather/extract overhead.
- Gate fast paths on both semantic format and concrete storage type. Palette
  images may contain index buffers; equal byte widths can still encode
  unrelated channel meanings. Preserve aliases, source normalization, clipping,
  and error order.

## Channel edits and pointwise transforms

- When alpha already exists, replace only the native alpha byte and preserve
  other bands. When an operation adds alpha, write directly into the required
  wider output once; remove avoidable input widening, not required output
  storage.
- For drawing contexts with a mode override, distinguish the effective context
  mode from the destination's stored format. Derive visible channel behavior
  from the public fallback and test that same override in the fast path.
- Before widening samples for a quantizer, check whether alpha participates in
  bucket coordinates, ordering, or output. Specialize channel count only when
  all three exclude the inactive band.
- Derive a simple byte transform on stored samples first. For a proven
  posterize rule with parameter `bits`, the byte mask is
  `sample & !((1 << (8 - bits)) - 1)`. Validate the allowed parameter range and
  reference semantics before specializing. If a quantized brightness factor
  maps exactly to a right shift, exhaust all 256 byte values and test vector
  tails before bypassing a lookup or generic vector adapter.
- Treat two-byte luminance/alpha as two different fields. A generic scalar
  channel loop can update the first byte and copy the second unchanged; a
  constant-alpha operation updates the second byte. Verify the logical mode
  before applying either rule.

## Scalar carriers and identity geometry

- A four-byte storage carrier may hold a scalar float or integer word rather
  than four color bands. Preserve logical type alongside physical storage.
  Copy raw bytes for an exact nearest-sample identity route only after proving
  coordinate selection and validating the same parameters/errors as the
  reference. Decode to the required scalar type for filtered arithmetic; keep
  byte order, precision narrowing, and accumulation order exact.
- Put identity geometry and no-op admission before materializing a resize or
  conversion result. Preserve the public copy/alias contract and test near
  identity geometry to ensure the branch does not bypass interpolation.
- For read-only operations over shared/cached data, inspect whether an accessor
  clones. Borrow immutable source storage where ownership allows; clone once
  before mutation when required.

## Pad, border, and fill operations

- Construct a native fill row once, repeat it to initialize the output, then
  copy the covered source span. When geometry makes the source span contiguous,
  copy it as one block; otherwise copy clipped rows and leave the remaining
  bands prefilled. Compare this simple memory path with parallel fill/copy.
- For three-byte channels, precompute a repeated fill pattern rather than
  deriving a channel index for every vector lane. Keep three-byte logical
  formats separate even when they share a physical buffer type.
- Map fill components by destination semantics. The same byte offset can hold
  alpha, a color component, or padding depending on output format.
- For compact GPU output stored in aligned words, make each word have one
  writer. A per-pixel kernel can race when neighboring pixels share an output
  word. Check grid limits, transfer lengths, and the final partial word.

## Fuse conversions only at exact boundaries

Compose per-sample stages into one pass only if the fused expression retains
every intermediate rounding, clamp, truncation, threshold, channel order, and
signed/unsigned conversion. Allocate the final buffer once where ownership
permits. Keep dithering, neighborhood filters, and recurrences separate unless
their state dependencies are preserved. Validate threshold-adjacent values,
channel-weighted samples, unusual ignored-looking channels, and exact public
output before measuring.
