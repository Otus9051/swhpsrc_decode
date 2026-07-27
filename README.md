# Sonarworks `.swhpsrc` File Architecture

## Overview
`.swhpsrc` files are proprietary binary files used by Sonarworks SoundID Reference for headphone calibration profiles. While they are undocumented, structural analysis reveals that they contain raw frequency response curves encoded as arrays of 64-bit floating-point numbers.

## File Structure

### Magic Header
The file starts with the ASCII string `PEQb`, identifying the format. This is typically followed by a small binary header (around 59 bytes) containing metadata, versioning, or hardware target identifiers (e.g., the string `Sonarworks`).

### Frequency Response Blocks
The core calibration data is stored in multiple sequential blocks of 24-byte triplets.
Each triplet consists of three 64-bit floats (Little-Endian Doubles):
1. **Frequency (Hz)**: Typical values range from 20.0 Hz to 22,000.0 Hz.
2. **Amplitude (dB)**: The raw frequency response gain at that frequency.
3. **Quality/Phase**: An unknown parameter, possibly representing filter Q-factor, phase, or an internal target modifier (often very close to 0 in standard profiles).

#### Block Breakdown
- **Block 0 (Starts at Offset 63)**: This is the primary frequency response curve. It contains approximately 355 to 356 data points, covering 20 Hz to 22 kHz. For "Average" profiles, this serves as the unified EQ curve. For individual profiles, this is likely the **Left Channel**.
- **Block 1 (Starts at Offset 8607)**: Contains another 356 triplets. In "Average" `.swhpsrc` files, this block is identical to Block 0. In individual headphone profiles, this is suspected to represent the **Right Channel**.
- **Block 2 (Starts at Offset 17151)**: Appears to be a zeroed block (amplitudes are 0.0), possibly a flat target reference or null phase placeholder.
- **Subsequent Blocks**: Other blocks follow sequentially (e.g., offsets 25695, 34239). Analysis indicates these might be offset variants (e.g., -3dB, +3dB) used for different Safe Headroom toggles or specific target modes inside the SoundID Reference software.

## Conversion to AutoEQ
Because the actual frequency and amplitude data are stored consecutively as raw floats, they can be directly parsed and exported into standard `frequency,raw` CSV files. These CSVs can then be natively processed by AutoEQ or imported into REW (Room EQ Wizard) to generate parametric EQ (PEQ) filters.
