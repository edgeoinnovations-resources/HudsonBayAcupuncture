# Hudson Valley Acupuncture Market Analysis Dashboard

An interactive Streamlit dashboard for exploring acupuncture market opportunities in the Hudson Valley region of New York State.

![Dashboard Preview](preview.png)

## Features

- **🗺️ Interactive Map**: Explore 113 municipalities with click-for-details popups, filterable by county, tier, and type
- **📊 Analytics**: Visual breakdowns of market tiers, county comparisons, and population vs. opportunity scatter plots
- **📋 Data Explorer**: Sortable, filterable data table with CSV export
- **📈 Top Opportunities**: Ranked list of best market opportunities with strategic insights
- **📄 Full Report**: Embedded PDF of the complete market analysis

## Data

The analysis covers:
- **10 Hudson Valley Counties**: Westchester, Rockland, Putnam, Orange, Dutchess, Ulster, Columbia, Greene, Albany, Rensselaer
- **113 Municipalities**: 18 cities + 95 villages
- **4 Market Tiers**: Based on Opportunity Score (combining market potential with population size)

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/acupuncture-market-analysis.git
cd acupuncture-market-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Deploy to Streamlit Cloud (Free)

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select your repository
6. Set main file path: `app.py`
7. Click "Deploy"

Your app will be live at: `https://YOUR_APP_NAME.streamlit.app`

## File Structure

```
acupuncture-market-analysis/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── data/
    ├── municipalities.geojson   # Combined cities + villages
    ├── counties.geojson         # County boundaries
    ├── cities.geojson           # City data only
    ├── villages.geojson         # Village data only
    └── Hudson_Valley_Acupuncture_Market_Analysis_Report_docx.pdf
```

## Methodology

The **Acupuncture Market Potential Index** is based on research showing typical acupuncture users are:
- Female (69.6% of users)
- Age 41-65 (47.4% of users)
- College educated (57.1%)
- Higher income households

**Index Components:**
| Component | Weight |
|-----------|--------|
| LifeMode Groups (Affluent Estates, Upscale Avenues, Uptown Individuals) | 30% |
| Education (Bachelor's+, Graduate, Some College, Associate's) | 25% |
| Female 35-64 as % of population | 25% |
| Households earning $75K+ | 20% |

**Opportunity Score** = (Normalized Index × 0.5) + (Normalized Market Size × 0.5)

## Key Findings

1. **Yonkers** is the #1 opportunity (Score: 75.3, Pop: 211,513)
2. **Westchester County** has the largest total addressable market
3. Small villages like **Nassau** (Index: 73.1) have high concentration but limited population
4. Population-weighting reveals opportunities missed by index alone

## License

This analysis was created for business planning purposes. Data sources include:
- New York State GIS Clearinghouse
- Esri ArcGIS Pro Enrich Layer (demographic and psychographic data)
- National Health Interview Survey (acupuncture user profiles)

---

Built with ❤️ using Streamlit, Folium, and Plotly
