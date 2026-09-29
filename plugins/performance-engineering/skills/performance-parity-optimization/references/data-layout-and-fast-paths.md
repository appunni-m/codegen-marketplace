# Data layout, representation, and exact fast paths

Load this reference when an operation converts between layouts, uses compact or
channelized data, materializes shared storage, or adds a guarded specialized
route.

## Trace semantic meaning and physical storage separately

Follow the public input through normalization, executor selection, and returned
output. At each boundary record logical format, concrete storage type, element
stride, active length, and requested result format. Classify every conversion
as an actual semantic conversion, same-layout clone, required output conversion,
typed-sample reinterpretation, or small helper. Function names and byte widths
alone do not prove that data was expanded.

Never infer channel roles from stride alone. For example, four-byte pixels may
represent RGBA, CMYK, padding, premultiplied color, or one 32-bit scalar sample;
two-byte pixels may store luminance and alpha. A logical mode override can
change operation semantics without changing the destination storage. Gate
specializations on both the operation contract and the concrete representation.

## Remove round trips and copies safely

- Start with same-format operations whose inputs are widened and later rebuilt
  into the original format. Preserve conversions that add a required output
  channel, resolve mixed-format rules, or affect public metadata.
- Inspect ownership before using a convenience accessor. A read-only accessor
  may clone a cached or shared buffer. Borrow immutable storage when allowed;
  clone once before mutation and preserve copy-on-write, alias, and lifetime
  rules.
- Check identity geometry or no-op mappings before creating an owned
  intermediate. Keep public validation and copy semantics even on a no-op path.
- For a direct row path, establish checked strides, clipping, and byte offsets
  once before the loop. Avoid accessors inside the loop if they convert,
  materialize, or clone.
- Compare a native byte loop with the generic/vector path. Preserve a general
  fallback for layouts or parameters the proof does not cover.

## Keep channel meaning exact

Use the selected logical band for mask coverage, then apply that coverage only
to the destination samples required by the operation. Preserve untouched alpha
or padding. Test binary masks, grayscale masks, color masks, premultiplied
formats, clipping, and aliases when those inputs are accepted. Treat alpha
placement as a property of the destination mode, not an assumed last byte for
every format.

For palette or quantization work, determine whether alpha participates in
coordinates, sorting, or output before expanding pixels. Specialize active
channels only when the inactive channel is proved irrelevant. For typed scalar
formats stored in a color-sized carrier, preserve the scalar's byte order and
rounding; do not reinterpret an unaligned byte pointer as a native float or
integer without satisfying alignment, endianness, and aliasing requirements.

## Preserve expression boundaries when fusing

Fuse consecutive pointwise stages only when each exact conceptual rounding,
clamp, threshold, and channel-order step can be reproduced in the final pass.
Allocate the final result once when ownership allows. Keep neighborhood filters,
error diffusion, cumulative recurrences, and other stateful stages separate
unless their dependencies and traversal are preserved.

Test threshold-adjacent and channel-weighted values, ignored-looking channels,
empty/small sizes, row tails, format variants, and side effects. Compare public
results and errors against the real reference route rather than checking only a
helper function.

For concrete pointwise, mask, paste, resize, and pad recipes—including packed
pixel tails—read [pixel-kernel recipes](pixel-kernel-recipes.md). Treat its
format examples as patterns; verify the active API's channel and rounding rules
before reusing one.
