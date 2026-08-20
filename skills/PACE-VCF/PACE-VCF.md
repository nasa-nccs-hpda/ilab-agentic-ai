# PACE-VCF Project Skills & Knowledge Base

## Project Goals

**Primary Goal**: Determine if we can create a Vegetation Continuous Fields (VCF) product using PACE-OCI hyperspectral data.

**Scientific Motivation**: 
- PACE-OCI offers unprecedented hyperspectral coverage (340-895 nm at 2.5 nm resolution + 7 SWIR bands)
- Hyperspectral data enables novel vegetation indices not possible with MODIS's discrete bands
- Red-edge indices (REIP, NDRE, CIRE, MTCI) are highly diagnostic for vegetation structure
- Pigment indices (CCI, PRI, mARI) capture physiological information beyond NDVI
- Goal is to assess whether these advantages translate to improved VCF accuracy

---

## Project Plan: 3-5 Experiments

### Experiment 1: MODIS Methodology Baseline
**Status**: ✅ Complete (baseline)

**Approach**:
- Use only MODIS-equivalent metrics (greenness-sorted, thermal-sorted, basic stats)
- Random Forest + Monte Carlo feature selection (matches original MODIS VCF methodology)
- Train against MODIS VCF reference data

**Purpose**: Establish baseline performance using traditional approach

---

### Experiment 2: MODIS + PACE Hyperspectral Metrics ⬅️ CURRENT
**Status**: 🔄 In Progress

**Approach**:
- Include all MODIS-equivalent metrics (Experiment 1)
- Add PACE-specific hyperspectral indices:
  - Red-edge: REIP, REP, NDRE, CIRE, MTCI
  - Pigment: CCI, PRI, mARI, ARI
  - Water/Structure: NDWI, NDII, GCI, EVI
- Add phenology-aware sorting (AltSort metrics)
- Add thermal metrics (VIIRS Band31 LST)
- Add snow-aware metrics
- XGBoost + Monte Carlo feature selection

**Purpose**: Quantify improvement from hyperspectral data

**Key Findings So Far**:
- REIP (Red Edge Inflection Point) is the #1 predictor
- Thermal metrics help distinguish bare ground from forest
- Snow-aware metrics improve accuracy in seasonal snow regions
- Full model R² ~0.76, RMSE ~13-14%

---

### Experiment 3: Deep Learning (CNN/U-Net)
**Status**: 📋 Planned

**Approach**:
- Use MODIS and PACE data as input layers
- CNN or U-Net architecture for spatial context
- Possibly explore other architectures (SVM, etc.)
- Train end-to-end on VCF prediction

**Purpose**: Leverage spatial patterns and deep feature learning

**Considerations**:
- Requires sufficient training data with spatial coverage
- May capture texture/context features missed by pixel-based methods
- Computational requirements higher than RF/XGBoost

---

### Experiment 4: PACE + Alpha Earth Embeddings (Optional)
**Status**: 📋 Planned (Optional)

**Approach**:
- Use Experiment 2 methodology as base
- Add Alpha Earth embeddings as additional features
- Alpha Earth provides pre-trained representations of Earth observation data

**Purpose**: Assess value of foundation model embeddings for VCF

---

### Experiment 5: Foundation Model (DINOv2/v3) (Optional)
**Status**: 📋 Planned (Optional)

**Approach**:
- Fine-tune a vision foundation model (e.g., DINOv2, DINOv3)
- Use PACE imagery as input
- Transfer learning approach

**Purpose**: Explore state-of-the-art foundation models for VCF prediction

---

## Rationale for Phenological Metrics (AltSort)

### Why New Sorting Approaches?

The original MODIS VCF methodology sorts composites by NDVI (greenness). The limitation is that this only uses MODIS-derived information. With PACE hyperspectral data, we can sort by indices that capture different aspects of vegetation that NDVI cannot.

### From Calendar-Based to Phenology-Based Metrics

**Discovery Process**:
1. Initially created **UnsortedMonthly metrics** (calendar-based: January, February, etc.)
2. Analyzed Random Forest models to see which monthly variables were important
3. **Identified the problem**: Calendar-based metrics don't work globally because:
   - Northern Hemisphere: Peak greenness in June-August
   - Southern Hemisphere: Peak greenness in December-February
   - Tropics: May have multiple or no distinct seasons
4. **Solution**: Created **phenology-based metrics** that automatically adapt to local growing seasons

**Key Insight**: By using phenological points (AtGreenUp, AtPeakNDVI, etc.) instead of calendar months, the metrics automatically account for hemisphere differences and work globally without manual adjustment.

### Why UnsortedMonthly is Now Excluded

```python
INCLUDE_UNSORTED = False  # Calendar-based metrics excluded
The phenology-based metrics (AltSort) replaced the need for calendar-based metrics because they:
Work in both hemispheres automatically
Adapt to local growing season timing
Are more scientifically meaningful (tied to plant physiology, not arbitrary dates)
Sorting by PACE Indices Instead of NDVI
Sort by REIP: Captures red-edge position, which is sensitive to chlorophyll content and canopy structure differently than NDVI. REIP's importance was identified from IGARSS conference research.
Sort by CCI: Captures chlorophyll/carotenoid ratio, indicating vegetation stress and seasonality
Sort by PRI: Captures photosynthetic light use efficiency
Phenological PointsThese metrics capture the timing of vegetation dynamics rather than just the values:MetricWhat It CapturesAtGreenUpSpring leaf-out / start of growing seasonAtPeakNDVIMaximum productivityAtMinNDVIDormant season / senescenceSenescenceFall transition periodSeasonalRangeAmplitude of phenological change (deciduous vs evergreen)Stress and Pigment-Based SortsThese capture vegetation physiological states beyond simple greenness:MetricWhat It CapturesHighChlorophyll3MeanWhen vegetation is healthiestHighCarotenoid3MeanStress or senescence (carotenoids increase relative to chlorophyll)HighAnthocyanin3MeanStress response or fall colorsMostStressed3MeanDrought/heat stress periodsLeastStressed3MeanOptimal growing conditionsGrowing Season Length (GSL)GSL was identified as an important feature from Random Forest models. It distinguishes:
Evergreen vs deciduous: Long GSL vs short GSL
Tropical vs temperate: Year-round vs seasonal
Desert vs vegetated: Minimal GSL vs substantial GSL
ThermalVegGSL: Combines thermal AND vegetation thresholds (LST > 280K AND NDVI > 0.3)
Current Pipeline (Experiment 2)Notebooks:
Notebook 2c/2e: Composite generation (32-day composites, 12 per year)
Notebook 3e: Metrics calculation (MODIS, PACE, AltSort, thermal, snow)
Notebook 6: Training (XGBoost + Monte Carlo feature selection)
Notebook 7: Inference and validation
Data Flow:PACE L3m (daily SURF REF) + VIIRS VNP21A2 (8-day LST)
        ↓
   Composites (2-Composites/)
        ↓
   Metrics TIFs (3-Metrics/)
        ↓
   Training Parquet
        ↓
   XGBoost Model
        ↓
   VCF Predictions
Success CriteriaExperimentSuccess MetricExp 1 (Baseline)Establish R², RMSE, MAE baselineExp 2 (PACE)Improvement over Exp 1 (target: +5% R²)Exp 3 (Deep Learning)Competitive or better than Exp 2Exp 4 (Alpha Earth)Added value from embeddingsExp 5 (Foundation)State-of-the-art comparisonKey Data SourcesPACE-OCI (Ocean Color Instrument)
Product Used: Daily Surface Reflectance (SURF REF) from L3m

Why SURF REF? The PACE vegetation index products don't document QA flag limits, so we use surface reflectance and calculate indices ourselves with known QA filtering


Spectral Range: 340-895 nm continuous (2.5 nm resolution) + 7 discrete SWIR bands (940-2260 nm)
SWIR Bands: 940, 1038, 1250, 1378, 1615, 2130, 2260 nm
Resolution: 2 km (native L3m)
Tilt: Performs tilt maneuver at sub-solar point to avoid sun glint
QA Filtering: Pre-filtered in L3m (ATMFAIL, CLDICE, HIGLINT, HILT, HISATZEN, HISOLZEN)
VIIRS (Visible Infrared Imaging Radiometer Suite)
Used for: Thermal data (LST - Land Surface Temperature)
Product: VNP21A2 (8-day LST composite)
Band 31: Thermal infrared (~11 μm)
Native Resolution: 1 km
Processing: Aggregated to 2 km to match PACE resolution
QA Filtering: QC_Day bits 0-1 (MODLAND_QA), bits 6-7 (LST accuracy)
MODIS VCF (Reference/Training Target)
Product: MOD44B Collection 6.1
Resolution: 250 m (aggregated to 2 km for PACE comparison)
Output: Percent Tree Cover (0-100%)
MODIS Band Mapping for PACEMODIS_BAND_RANGES = {
    'Band_1': (620, 670),   # Red
    'Band_2': (841, 876),   # NIR  
    'Band_3': (459, 479),   # Blue
    'Band_4': (545, 565),   # Green
    'Band_5': (1230, 1250), # SWIR1 - use PACE 1249 nm
    'Band_6': (1610, 1652), # SWIR2 - use PACE 1618 nm (expanded range!)
    'Band_7': (2105, 2155), # SWIR3 - use PACE 2131 nm
}
Important: Band_6 range must be (1610, 1652) not (1628, 1652) to capture PACE's 1618 nm wavelength.Scaling Conventions (Int16 Storage)NO_DATA = -10001

def scale_reflectance(data):
    """Reflectance (0-1) → Int16: multiply by 10,000"""
    scaled = data * 10000
    return np.where(np.isfinite(scaled), scaled, NO_DATA).astype(np.int16)

def scale_ndvi(data):
    """NDVI/indices (-1 to 1) → Int16: multiply by 1,000"""
    scaled = data * 1000
    return np.where(np.isfinite(scaled), scaled, NO_DATA).astype(np.int16)

def scale_thermal(data):
    """Temperature (Kelvin) → Int16: multiply by 100"""
    scaled = data * 100
    return np.where(np.isfinite(scaled), scaled, NO_DATA).astype(np.int16)

def scale_index(data):
    """Generic index (-1 to 1) → Int16: multiply by 1,000"""
    scaled = data * 1000
    return np.where(np.isfinite(scaled), scaled, NO_DATA).astype(np.int16)
Critical Metric Categories1. PACE Hyperspectral Indices
REIP (Red Edge Inflection Point): #1 predictor for tree cover
CCI (Chlorophyll/Carotenoid Index): Pigment ratio
PRI (Photochemical Reflectance Index): Stress indicator
NDRE (Normalized Difference Red Edge)
CIRE (Chlorophyll Index Red Edge)
MTCI (MERIS Terrestrial Chlorophyll Index)
2. Thermal Metrics (Band31 from VIIRS)
Source: VIIRS VNP21A2, aggregated from 1 km to 2 km
Basic stats: Min, Max, Mean, Median, Amplitude
Temperature-sorted: Warmest3/6/8, Coolest3/6
Phenology-linked: ThermalAtPeakNDVI, ThermalAtMinNDVI
Growing season: LST-GrowingSeasonCount, ThermalVegGSL
3. Snow-Aware Metrics
NDSI = (Green - SWIR) / (Green + SWIR), threshold > 0.4 for snow
Snow counts: Snow-CompositeCount, Snow-FreeCompositeCount
Snow-free values: SnowFree-Band_7-, SnowFree-LST-, SnowFree-NDVI-*
Timing: SnowFree-FirstComposite, LST-AtFirstSnowFree
4. Phenology Metrics (AltSort)
Phenology points: AtGreenUp, AtPeakNDVI, AtMinNDVI, Senescence
Season length: GrowingSeasonLength, GSL-gt-02/04/05
Integrated: IntegratedNDVI
NaN Handling Best PracticesProblem: Thermal data has gapsVIIRS thermal coverage is often lower than PACE optical coverage due to different orbits, cloud masking, and QA filtering.Solutions Applied:1. For sorted metrics (warmest/coolest):# Replace NaN with -inf for warmest (sorts to beginning, ignored)
thermal_for_warmest = np.where(np.isfinite(thermal_cube), thermal_cube, -np.inf)
# Replace NaN with +inf for coolest (sorts to end, ignored)
thermal_for_coolest = np.where(np.isfinite(thermal_cube), thermal_cube, np.inf)
2. For phenology-indexed values (thermal at peak NDVI):# Fallback to mean if specific composite has no thermal data
thermal_at_peak = thermal_cube[peak_ndvi_idx, i_idx, j_idx]
thermal_mean = np.nanmean(thermal_cube, axis=0)
thermal_at_peak = np.where(np.isfinite(thermal_at_peak), thermal_at_peak, thermal_mean)
3. For snow metrics in no-snow regions:# Detect no-snow region
is_snow_region = snow_pct >= 1.0

if not is_snow_region:
    # SnowFree metrics = regular metrics (everything is snow-free)
    metrics['SnowFree-LST-Max'] = scale_thermal(np.nanmax(thermal_cube, axis=0))
    # LST-AtFirstSnowFree = first VALID thermal, not first composite
    metrics['LST-AtFirstSnowFree'] = scale_thermal(get_first_valid(thermal_cube))
4. Helper function for first valid value:def get_first_valid(cube):
    """Get first valid (non-NaN) value for each pixel across time."""
    H, W = cube.shape[1], cube.shape[2]
    result = np.full((H, W), np.nan, dtype=np.float32)
    for t in range(cube.shape[0]):
        needs_fill = np.isnan(result) & np.isfinite(cube[t, :, :])
        result = np.where(needs_fill, cube[t, :, :], result)
        if np.all(np.isfinite(result)):
            break
    # Fallback to mean if still NaN
    result = np.where(np.isfinite(result), result, np.nanmean(cube, axis=0))
    return result
Training ConfigurationBalanced SamplingTARGET_BARE_PCT = 0.25      # Bare ground (0%)
TARGET_LOW_PCT = 0.25       # Low vegetation (1-25%)
TARGET_FOREST_PCT = 0.08    # Dense forest (81-100%) - UPSAMPLE
# Medium (26-50%) and High (51-80%) kept as-is
Monte Carlo Feature SelectionN_TRIALS = 100
FEATURES_PER_TRIAL = 50
MIN_FEATURE_USAGE = 10
TOP_N_FEATURES = 50  # Increased from 30 for better coverage
XGBoost ParametersXGB_PARAMS = {
    'tree_method': 'gpu_hist',
    'n_estimators': 500,
    'max_depth': 10,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42,
}
Feature Exclusions# Exclude from training:
# 1. QA metrics (diagnostic only, cause data leakage)
qa_features = [c for c in feature_cols if 'QA_' in c]

# 2. UnsortedMonthly (calendar-based, replaced by phenology-based metrics)
INCLUDE_UNSORTED = False
Known Issues & SolutionsIssue: Desert/Arid OverpredictionSymptom: Model predicts 15-20% tree cover in deserts (should be 0%)
Cause: Thermal metrics (LST-GrowingSeasonCount) are high in both deserts and tropical forests
Solution: Post-processing arid correction or add explicit arid indicator featuredef apply_arid_correction(predictions, lst_mean, lst_range, ndvi_max):
    """Cap predictions in arid regions."""
    arid_mask = (lst_mean > 295) & (ndvi_max < 0.25) & (lst_range > 15)
    predictions[arid_mask] = np.minimum(predictions[arid_mask], 5.0)
    return predictions
Issue: Low Valid Pixel Count in TropicsSymptom: Amazon tiles have few valid pixels
Cause: Persistent cloud cover → missing optical data; thermal gaps from VIIRS
Solution: Fill NaN with median values, use >80% threshold for invalidityIssue: Negative Correlation in Some TilesSymptom: h12v04 (Eastern US forests) has negative correlation
Cause: Model undertrained on dense forest; feature mismatch
Solution: Increase TARGET_FOREST_PCT, increase TOP_N_FEATURESIssue: Band_6 has 0% valid dataSymptom: All Band_6 metrics are completely invalid
Cause: PACE 1618 nm wavelength falls outside original Band_6 range (1628-1652)
Solution: Expand Band_6 range to (1610, 1652)File Structure/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/
├── output/
│   └── {tile}/
│       └── {year}/
│           ├── 1-Downloads/          # Raw PACE/VIIRS data
│           ├── 2-Composites/
│           │   ├── aggregated/       # MODIS-equivalent bands (from PACE)
│           │   ├── wavelengths/      # Individual PACE wavelengths
│           │   └── thermal/          # VIIRS Band31 (aggregated to 2km)
│           └── 3-Metrics/
│               ├── MODIS_Metrics.tif    # ~300 bands
│               ├── PACE_Metrics.tif     # ~146 bands
│               └── PACE_AltSort_Metrics.tif  # ~246 bands
├── models/
│   ├── training_data_*.parquet
│   ├── pace_vcf_mc_xgb_*.json
│   └── mc_top_features_*.txt
└── inference/
    ├── PACE_VCF_{year}_{tile}_2km.tif
    └── MODIS_VCF_{year}_{tile}_2km.tif
Diagnostic CommandsCheck metric validity:with rasterio.open(metrics_path) as src:
    for i, name in enumerate(src.descriptions):
        data = src.read(i + 1)
        valid_pct = 100 * np.sum(data != -10001) / data.size
        if valid_pct < 99:
            print(f"{name}: {valid_pct:.1f}% valid")
Check composite coverage:data = np.fromfile(composite_path, dtype=np.int16).reshape(600, 600)
valid = np.sum(data != -10001)
print(f"Valid: {valid:,} / 360,000 ({100*valid/360000:.1f}%)")
Check training feature counts:thermal = [c for c in feature_cols if 'LST' in c or 'Band31' in c]
snow = [c for c in feature_cols if 'Snow' in c]
print(f"Thermal features: {len(thermal)}")
print(f"Snow features: {len(snow)}")
Expected PerformanceMetricFull Model (500+ features)MC Model (50 features)R²~0.76-0.77~0.72-0.76RMSE~13-14%~14-15%MAE~9-10%~10-11%Per-Tile Expectations:
Good tiles (h10v05, h31v11): R² > 0.45, Correlation > 0.6
Challenging tiles (deserts, tropics): May have lower correlation due to biome-specific issues
Test TilesTileRegionCharacteristicsh09v05California/NevadaMixed forest, shrubland, deserth10v05Western USRocky Mountains, diverse terrainh12v04Eastern USDense deciduous foresth12v09AmazonTropical rainforest, high cloud coverh18v04EuropeMixed forest, agricultureh20v06Middle EastArid/deserth21v06Arabia/SaharaExtreme deserth31v11New ZealandTemperate forest, mixed land cover