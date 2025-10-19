# LogamMulia Stock Checker

Automated tool to check gold availability across LogamMulia branches in Indonesia for thesis research.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Basic Usage

**Check specific gold weight across branches:**

```bash
python stock_analyzer.py --weight 1.0 --quick --max-branches 5
```

**Check specific branches:**

```bash
python stock_analyzer.py --branches ASB1 ABDG AJK2 --export both
```

**Check all major branches:**

```bash
python stock_analyzer.py --export both
```

**Debug stock detection for a branch:**

```bash
python stock_analyzer.py --debug-branch ASB1
```

## Available Branches

| Code | City | Branch Name |
|------|------|-------------|
| ASB1 | Surabaya | Surabaya Darmo |
| ABDG | Bandung | Bandung |
| AJK2 | Jakarta | Gedung Antam |
| AJK4 | Jakarta | Setiabudi One |
| ASMG | Semarang | Semarang |
| AJOG | Yogyakarta | Yogyakarta |
| AKNO | Medan | Medan |
| ADPS | Bali | Denpasar Bali |
| AMKS | Makassar | Makassar |
| APLG | Palembang | Palembang |
| APKU | Pekanbaru | Pekanbaru |

*All 21 branches available. Use `branch_parser.py` to see complete list.*

## Command Options

- `--weight <grams>`: Check specific gold weight (0.5, 1.0, 2.0, 5.0, 10.0, etc.)
- `--branches <CODE1 CODE2>`: Check specific branch codes
- `--max-branches <N>`: Limit number of branches to check
- `--export <format>`: Export results (csv, json, both)
- `--quick`: Fast check mode
- `--debug-branch <CODE>`: Debug stock detection for specific branch
- `--shipping-only`: Check only branches that can ship via courier

## Examples

**Find 1 gram gold availability:**

```bash
python stock_analyzer.py --weight 1.0 --quick --max-branches 8
```

**Compare Jakarta and Surabaya:**

```bash
python stock_analyzer.py --branches AJK2 ASB1 --export csv
```

**Check investment sizes (5g, 10g):**

```bash
python stock_analyzer.py --weight 5.0 --export json
python stock_analyzer.py --weight 10.0 --export json
```

## Output Files

- `stock_availability_report_[timestamp].json` - Complete data
- `stock_availability_report_[timestamp].csv` - Excel-ready format

## Stock Status

- ✅ **Available**: Product is in stock
- ⚠️ **Limited Stock**: Limited availability  
- ❌ **Out of Stock**: "Belum tersedia" - not available

## Features

- ✅ **403 Bypass**: Advanced retry system handles website protection
- ✅ **Real-time Data**: Live stock and pricing information
- ✅ **All Branches**: 21 branches across 15 Indonesian cities
- ✅ **Rate Limiting**: Responsible access with delays
- ✅ **Debug Mode**: Verify stock detection accuracy

## Troubleshooting

**403 Errors**: Automatically handled with 5 retry attempts  
**No Data**: Check branch code with `branch_parser.py`  
**Debug Issues**: Use `--debug-branch` to see detection details

---

**For academic research purposes. Use responsibly and in accordance with website terms of service.**
