# Neural compression quantizer specification

**Status:** experimental component; not yet connected to an arithmetic coder or neural codec.

## Integer CDF construction

For n symbols, configured total T, and minimum frequency m:

1. Reserve m counts for each symbol.
2. Compute the remaining budget R = T - n*m.
3. Normalize the non-negative probability weights.
4. Allocate floor(p[i] * R) additional counts.
5. Distribute the unassigned remainder by descending fractional part (largest remainder).
6. Break equal fractional-remainder ties by ascending symbol index.

The resulting frequencies sum exactly to T; every symbol receives at least m. A zero-mass input is treated as uniform. T, m, shape, and probability values are validated.

The implementation uses float64 normalization and int64 frequency/CDF arrays. Deterministic tie-breaking is part of the format contract. This does not by itself guarantee bit-identical neural probabilities across different machines.

## Probability-floor cost

For a 256-symbol alphabet, m = 1, and a perfectly certain prediction, the chosen symbol receives T - 255 counts. Its minimum idealized coding cost is:

    -log2((T - 255) / T)

| CDF total | Peak frequency | Idealized floor |
|---:|---:|---:|
| 4,096 | 3,841 | approximately 0.0927 bits/symbol |
| 65,536 | 65,281 | approximately 0.00562 bits/symbol |

These are probability-quantization costs, not measured end-to-end codec rates. Actual coder overhead, model errors, and framing add to the final size.

## Configuration policy

- Keep total=4096 as the current experimental default.
- Treat total and min_freq as explicit codec configuration and serialize them in any future stream header.
- Do not change the default to 65,536 until the arithmetic coder has passed round-trip, skewed-distribution, long-stream, changing-CDF, and 32-bit-boundary tests at that total.
- Do not claim cross-machine bitstream determinism until it is tested independently.
