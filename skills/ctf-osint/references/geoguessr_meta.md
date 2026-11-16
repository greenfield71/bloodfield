# GeoGuessr & Global Infrastructure Heuristics (CTF OSINT 2025–2026)

When an OSINT challenge provides a photo or Street View screenshot without readable signage, business names, or GPS metadata, visual infrastructure heuristics allow analysts to pinpoint the exact country, region, and camera generation.

---

## 1. Utility Poles & Power Infrastructure

Utility poles are among the most reliable regional indicators because national electric grids use standardized materials and installation codes.

| Pole Type / Feature | Distinctive Visual Characteristics | Typical Countries / Regions |
|---------------------|-----------------------------------|-----------------------------|
| **Perforated Concrete (Round Holes)** | Concrete pole with evenly spaced circular holes drilled along the shaft | **Poland** (ubiquitous "Żerdź wirowana"), occasional Baltic states |
| **Perforated Concrete (Rectangular / Ladder Holes)** | Heavy concrete pole with rectangular ladder-style cutout rungs | **France** (very common), **Romania**, **Hungary**, **Ukraine**, **Brazil** |
| **A-Frame Wooden Pole** | Two wooden poles joined at top forming an "A" or triangle shape | **United Kingdom**, **Ireland**, **Sweden**, **Norway**, **Finland** |
| **Metal Step / Climber Rungs** | Wooden or concrete poles with alternating metal climbing pegs protruding from sides | **Japan** (very common), **Taiwan** |
| **Yellow & Black Diagonal Striped Base** | Reflective yellow and black diagonal striped wrapping/paint on bottom 2 meters | **Taiwan** (nearly universal on rural poles) |
| **Vertical Stenciled Serial Numbers** | Vertical metal plates with stamped black letters/numbers on silver backing | **South Korea**, **Japan** (often with regional electric company badge, e.g. TEPCO) |
| **Hollow Metal / Octagonal Poles** | Thin steel hollow poles, galvanized grey | **Australia**, **New Zealand**, **Israel** |
| **Heavy Wooden Crossarms** | Square-cut dark treated lumber with multiple horizontal crossarms and ceramic insulators | **United States**, **Canada**, **Australia** |

---

## 2. Roadside Bollards & Delineators

Roadside guideposts (bollards) are strictly regulated by national transport ministries. Their colors, reflective patches, and shapes instantly identify the country.

| Country | Bollard Shape | Body Color | Top Cap | Front Reflector | Back Reflector |
|---------|---------------|------------|---------|-----------------|----------------|
| **Germany** | Rectangular with rounded front | White | Angled Black | Vertical White strip | Two round White dots |
| **Austria** | Rectangular with flat top | White | Flat Black | Vertical Red strip (Left), White (Right) | Reversible |
| **France** | Cylindrical / Round post | White | Flat White | Red retroreflective ring (curves) or White | White |
| **United Kingdom** | Cylindrical or square post | White | Black or White | Red reflector (Left), White (Right) | Amber (motorway) |
| **Norway** | Flat rectangular paddle | White | Black cap | Vertical White strip on yellow backer | White |
| **Sweden** | Round / curved post | White | Flat top | Orange rectangular reflector | White rectangular |
| **Finland** | Flat paddle | White | Black top | White rectangular reflector | White rectangular |
| **Poland** | Curved post | White | Red slanted band | Red rectangular reflector on red band | White on opposite |
| **Italy** | Cylindrical post | White | Black top | Red reflector (Right), White (Left) | White |
| **Spain** | Wide flat blade | White | Black band | Yellow/White reflector | White |
| **Turkey** | Cylindrical with diagonal top | White | Diagonal slice | Red rectangular reflector | White |
| **Australia** | Flexible plastic guidepost | White | Flat top | Red strip/reflector (Left), White (Right) | Reversible |
| **New Zealand** | Wooden or plastic post | White | Red band | Red reflector (Left), White (Right) | Reversible |
| **Russia / CIS** | Flat or round post | White | Slanted Black top | Black horizontal stripe at base, Red/White reflector | Red/White |

---

## 3. License Plates

Vehicle registration plates narrow down jurisdiction immediately:

### 3.1. European Union Standard
- Long rectangular white plate with a **blue strip on the left** containing the European circle of stars and country code letter (e.g. `D`, `F`, `PL`, `I`, `E`).
- **Italy & France**: Have a second blue strip on the right side indicating the department/region code.

### 3.2. Yellow License Plates
- **United Kingdom**: Front plate is **White**, Rear plate is **Yellow**.
- **Netherlands**: Both front and rear plates are bright **Yellow** with a blue EU strip.
- **Luxembourg**: Both front and rear plates are **Yellow** with an EU strip.
- **Israel**: Front and rear plates are bright **Yellow** with a blue strip on the left (Israeli flag).
- **Colombia**: Public transport vehicles, taxis, and commercial trucks have bright **Yellow** plates.
- **Cyprus**: Pre-2013 rear plates are yellow (front white); newer are white with EU strip.

### 3.3. Distinctive Colors & Badges
- **Belgium**: White plate with **Red lettering** and red border (EU strip on modern plates).
- **Norway**: Standard cars have white plates; **Green plates** indicate 2-seat commercial vans.
- **Switzerland**: Smaller front plate, rear plate contains canton coat of arms on left and Swiss shield on right.
- **Japan**: Standard passenger cars have **White plates with Green text**; Kei-cars (microcars) have **Yellow plates with Black text**; commercial vehicles have **Green plates with White text**.
- **United States / Canada**: Rectangular 12x6 inch plates; varied state graphics, slogan text, and registration stickers.

---

## 4. Road Markings & Traffic Signage

### 4.1. Centerline Markings
- **Yellow Centerlines**:
  - **Americas**: United States, Canada, Mexico, Brazil, Colombia, Argentina, Chile.
  - **Asia**: Japan, South Korea, Taiwan, Philippines, Thailand.
  - **Europe Exception**: **Norway** uses yellow centerlines (the only European country besides Iceland on certain passes).
- **White Centerlines**:
  - Almost all of **Europe** (UK, France, Germany, Spain, Italy, Poland, etc.).
  - **Australia** and **New Zealand**.
  - **Russia** and CIS nations.

### 4.2. Outer Road Edges
- **Dashed White Outer Edges**: **Sweden**, **Norway**, **Denmark**.
- **Solid White Outer Edges**: France, Germany, Spain, Poland, Italy, UK.
- **Yellow Outer Edges**: **South Africa**, **Botswana**, **Eswatini**, **Lesotho**, **Ireland** (broken yellow line along road shoulders).

### 4.3. Chevron Signs (Sharp Curve Warnings)
- **Red arrow on White background**: UK, France, Spain, Poland, Turkey, Greece.
- **White arrow on Blue background**: Germany, Austria, Czechia, Slovakia.
- **Yellow arrow on Black background**: USA, Canada, Australia, New Zealand, Japan, Malaysia.
- **Yellow / Orange arrow on Blue background**: Norway, Sweden, Finland.

---

## 5. Google Street View Camera Generations & "Car Meta"

Google has mapped the world using four distinct camera systems. Identifying the camera generation immediately dates the imagery or rules out certain countries.

### 5.1. Camera Generations
| Generation | Active Era | Resolution & Visual Artifacts |
|------------|------------|-------------------------------|
| **Gen 1** | 2007–2008 | Extremely low resolution, blurry faces, primitive stitching, US only. |
| **Gen 2** | 2008–2010 | Low-to-medium resolution; severe **purple / magenta fringing** (chromatic aberration) along rooflines and tree branches; circular sky artifact. |
| **Gen 3** | 2011–2019 | Sharp high definition, circular blurred disc on the car roof / hood, natural color saturation. |
| **Gen 4** | 2017–Present | Ultra HD (4K), vibrant high dynamic range, smaller car blur, occasionally visible vehicle pickup bed or roof bars. |

### 5.2. Iconic Google Car Meta (Country Identifiers)
When looking straight down (or backward) at the Google vehicle in Street View:

- **Kenya**:
  - Prominent black **air snorkel** visible on the front right hood.
  - Distinct roof rack with black tape on the bars.
- **Nigeria**:
  - **Police Escort Vehicle**: A police pickup truck or sedan with flashing roof lights is visible either directly in front of or behind the Google car in almost all Nigerian coverage.
- **Ghana**:
  - Roof rack with a piece of **black electrical tape** wrapped around the front-right bar.
- **Senegal**:
  - Roof rack with distinctive blue or black straps tied to the vehicle crossbars.
- **Mongolia**:
  - Roof rack with large silver camping bars; Google car is often a white pickup truck with open bed visible.
- **Guatemala**:
  - Roof rack with prominent side mirrors visible when looking directly downward.
- **Kyrgyzstan**:
  - White car with prominent roof rack and visible antenna mounting bracket.
- **Curaçao & Bermuda**:
  - Distinctive roof rack structures and bright island utility infrastructure.

---

## 6. Driving Side Matrix (Left-Hand vs. Right-Hand Traffic)

Determining whether cars drive on the left or right immediately eliminates ~70% of the world.

### Left-Hand Traffic (Drive on the LEFT):
- **Europe**: United Kingdom, Ireland, Cyprus, Malta, Isle of Man, Channel Islands.
- **Asia**: Japan, Singapore, Malaysia, Thailand, Indonesia, India, Pakistan, Bangladesh, Sri Lanka, Nepal, Bhutan, Brunei, Hong Kong, Macau.
- **Oceania**: Australia, New Zealand, Papua New Guinea, Fiji, Samoa, Solomon Islands, Tonga.
- **Africa**: South Africa, Namibia, Botswana, Zimbabwe, Mozambique, Zambia, Malawi, Tanzania, Kenya, Uganda, Eswatini, Lesotho, Mauritius, Seychelles.
- **Americas / Caribbean**: Guyana, Suriname, Jamaica, Bahamas, Barbados, Trinidad & Tobago.

### Right-Hand Traffic (Drive on the RIGHT):
- All of continental Europe, North America (USA, Canada, Mexico), Central & South America (except Guyana/Suriname), North & Central/West Africa, Middle East, and mainland China.
