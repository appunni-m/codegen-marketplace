# GPU and accelerator patterns

Load this reference for GPU, DSP, FPGA, or other offload work, particularly
when dispatch, data movement, or asynchronous completion may affect the result.

## Time the path that the caller sees

Separate host preparation, allocation, upload, submission, device queueing,
device execution, synchronization/mapping, readback, and host output creation.
Use device timestamps for the kernel and a system timeline or completion timer
for the complete operation. A map/wait interval can include queued device work
and synchronization as well as the transfer itself.

Record actual dispatches, fallbacks, transfer bytes, output bytes, conversions,
and completion. Obtain a receipt for each tested case where possible. A profile
label or successful host compilation does not prove that the intended kernel
ran; lazy pipeline creation can fail only at runtime.

## Follow the data before tuning the kernel

- Count input, intermediate, and output bytes separately. A compact upload does
  not make a compact result if the shader and readback still use the wider
  representation.
- Keep data device-resident across compatible stages. Fuse or batch only when
  the public result and intermediate rounding permit it, and when extra waits,
  scratch memory, and queue occupancy fit the target.
- Compare the complete offload route with CPU/SIMD over the same workload. Use
  a measured host crossover for small work when launch and transport dominate.
- Stop tuning arithmetic when the observed transport, queue, mapping, or output
  cost is larger. Record the remaining floor and measure a separate next step.

## Make layout and bounds explicit

- Admit a device path on logical meaning, concrete storage layout, dimensions,
  alignment, length, parameters, supported features, and batch shape as needed.
  Never infer semantic channels from bytes per pixel alone: padding, alpha,
  premultiplied values, color components, and scalar words can have the same
  stride.
- Check every size multiplication, offset, padded length, binding limit, grid
  axis, and active output span before dispatch. Fall back before upload when a
  host layout or device limit is unsupported.
- Assign disjoint output ownership. If the storage interface writes aligned
  words, give each output word one writer or use a synchronization primitive
  required by that memory model; neighboring logical pixels can share a word.
- Treat padded tails as transport storage, not valid output. Trim readback to
  the checked public length and prove every shader read stays in bounds.
- Validate shader compilation/pipeline creation before diagnosing output
  mismatches. Keep format-specific packing and unpacking in named, tested
  helpers instead of overloading unrelated uniforms or metadata fields.

## Packed three-byte input example

For tightly packed three-byte pixels read from little-endian 32-bit words, a
pixel begins at byte offset `3 * pixel_index`. Compute `word_index = offset >>
2` and `shift = (offset & 3) * 8`. Extract `((word[word_index] >> shift) | (next
word << (32 - shift))) & 0x00ff_ffff` only when the pixel crosses a word boundary
(`shift > 8`); otherwise the current word contains all three bytes. Check
`width * height * 3`, the exact input length, and padded upload length before
dispatch. Read the next word only when all bytes needed by that pixel are valid.
Exercise short widths and final pixels that use a partially filled last word.

This layout is worth testing only when the complete operation benefits from
three-byte transport. If output uses four-byte words, measure that unavoidable
readback separately. For a compact three-byte output stored in words, assign
one invocation to each aligned destination word; per-pixel writers can overlap
the same word at channel boundaries.
