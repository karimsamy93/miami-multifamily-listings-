# 🚀 Deployment and Automated Workflow Instructions

Here is your complete guide to publishing your data, deploying the Interactive Dashboards to GitHub Pages, connecting your custom domain, and integrating the Google Sheets export into your Python workflow.

---

## 1. Publishing your Google Sheet as a CSV URL

For the Dashboards to fetch your listing data continuously, your Google sheets need to be published as a live CSV link.

1. Open your Miami Multifamily or Condo Google Sheet.
2. Ensure you have a **"Last Updated"** column. (At minimum, the first row needs the date populated, e.g., `March 12, 2026`).
3. In the top menu, go to **File** > **Share** > **Publish to web**.
4. In the dialogue:
   - Instead of "Entire Document", select your specific **Sheet** (e.g., "Sheet1" or "Multifamily Listings").
   - Instead of "Web page", select **Comma-separated values (.csv)**.
5. Click **Publish** and copy the generated link.
6. Open your local `index.html` (for multifamily) or `condos.html` (for condos) in a text editor.
7. Locate the configuration section at the bottom of the HTML (`<script>` block) and paste the URL.
   ```javascript
   const SHEET_CSV_URL = "YOUR_GOOGLE_SHEET_CSV_URL_HERE";
   ```

---

## 2. Deploying to GitHub Pages

Once your HTML files are configured with the CSV URLs, it's time to upload them to your repository: `https://github.com/karimsamy93/miami-multifamily-listings-`

### A. Uploading the Files
1. Go to your GitHub repository in your browser.
2. Click the **Add file** dropdown, then select **Upload files**.
3. Drag and drop both `index.html` and `condos.html` into the box.
4. Scroll down and click the green **Commit changes** button.

### B. Enabling GitHub Pages
1. On your repository page, click the **Settings** tab.
2. In the left sidebar, click on **Pages**.
3. Under **Source**, ensure it's set to **Deploy from a branch**.
4. Under the **Branch** section, select `main` (or `master`) and keep the folder as `/ (root)`.
5. Click **Save**. Within a few minutes, GitHub will build your site.

### C. Setting up the Custom Domain
To host your pages at `listings.miamimultifamilymin.com`:

1. Still on the **Pages** settings page, scroll down to the **Custom domain** section.
2. Type in `listings.miamimultifamilymin.com` and click **Save**.
   *(GitHub will automatically create a file called `CNAME` in your repository containing this domain).*
3. Next, head over to your Domain Registrar or DNS Provider (where you purchased `miamimultifamilymin.com`, e.g., Namecheap, Cloudflare, GoDaddy).
4. Go to the DNS settings and add a **CNAME Record**:
   - **Type:** `CNAME`
   - **Host/Name:** `listings`
   - **Value/Target:** `karimsamy93.github.io`
   - **TTL:** Automatic or 1 Hour
5. Save the DNS record. It may take up to 24–48 hours to fully propagate worldwide, though it usually takes 10–15 minutes.

### D. Enabling HTTPS
Once your DNS is fully propagated and GitHub verifies the connection:
1. Go back to your GitHub repository's **Settings > Pages**.
2. Make sure the checkbox for **Enforce HTTPS** is selected.

---

## 3. Python Automation Workflow Updates

Since you are already using a Google Drive service account, you just need to add sheet-writing capabilities.

### A. Update OAuth Scopes
Ensure your Python auth flow is requesting the `spreadsheets` scope alongside `drive`:
```python
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]
```

### B. Python Function to Write the DataFrame
You can use `gspread` alongside your `pandas` dataframe to seamlessly push data every time your script runs. 

If you don't have `gspread` installed, run: `pip install gspread`.

```python
import gspread
from datetime import datetime

# Assuming you already have an authorized credentials object (e.g., 'creds')
# client = gspread.authorize(creds)

def export_df_to_google_sheet(client, df, spreadsheet_key, sheet_name="Sheet1"):
    """
    Overwrites a Google Sheet with a Pandas DataFrame.
    Automatically handles formatting for the Dashboard 'Last Updated' requirements.
    """
    
    # 1. Add "Last Updated" column so the HTML Dashboard can read it
    df['Last Updated'] = datetime.now().strftime("%B %d, %Y")
    
    # 2. Reorder columns so 'Last Updated' is the very last column (optional but clean)
    cols = df.columns.tolist()
    cols.insert(len(cols), cols.pop(cols.index('Last Updated')))
    df = df[cols]
    
    # 3. Handling NaN values: Google Sheets API throws errors on NaNs
    df = df.fillna("")
    
    # 4. Open the Spreadsheet and Sheet
    spreadsheet = client.open_by_key(spreadsheet_key)
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
        
    # 5. Clear the existing contents completely
    worksheet.clear()
    
    # 6. Prepare data for upload (headers on first row, values below)
    data = [df.columns.values.tolist()] + df.values.tolist()
    
    # 7. Update the sheet
    worksheet.update(values=data, range_name='A1')
    print(f"Successfully pushed {len(df)} rows to {sheet_name}.")

# ----------------------------
# EXAMPLES USAGE
# ----------------------------
# # Extract your spreadsheet ID from its URL
# # For https://docs.google.com/spreadsheets/d/1BxiMVs0X2.../edit
# SPREADSHEET_ID = '1BxiMVs0X2...'
# 
# export_df_to_google_sheet(client, final_multifamily_df, SPREADSHEET_ID, "Multifamily")
```

With this function integrated, every time your script runs naturally, it replaces the entire target sheet with the latest scored properties, calculates the specific date of the run, and sets it on the `"Last Updated"` column. The published CSV automatically updates in real-time, instantly reflecting on your interactive Dashboards!
