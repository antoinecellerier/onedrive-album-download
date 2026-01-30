# OneDrive API Metadata Discovery Results

## Summary

Tested the Microsoft Graph API (both `/v1.0` and `/beta` endpoints) to discover any undocumented AI-generated metadata fields. **No AI-generated captions, tags, labels, faces, or focus points were found.**

## Tests Performed

1. **Beta API with `$select=*`** - Request all available fields
2. **Beta API with `$expand`** - Expand related resources
3. **Specific AI field names** - Explicitly requested: tags, caption, labels, faces, objects, text, insights, aiMetadata, computerVision, searchableText
4. **Children with all metadata** - Get image items with all fields
5. **Thumbnails endpoint** - Check for analysis data in thumbnails
6. **Analytics endpoint** - Check for insights/analytics
7. **Search API** - Check if search exposes AI tags
8. **Everything expanded** - Request all expansions at once

## Available Metadata Fields

### OneDrive-Specific (Not in Image Files)
- `createdDateTime` - Upload date to OneDrive
- `lastModifiedDateTime` - Last modified in OneDrive
- `createdBy` / `lastModifiedBy` - User/application info
- `shared` - Sharing permissions and scope
- `webUrl` - OneDrive web link
- `mediaAlbum.albumItemCount` - Number of items in album

### Already in Image Files (EXIF Data)
- `image.width` / `image.height` - Dimensions
- `photo.cameraMake` / `photo.cameraModel` - Camera info
- `photo.takenDateTime` - When photo was taken
- `photo.focalLength` / `photo.iso` / `photo.fNumber` - Camera settings
- `photo.exposureDenominator` / `photo.exposureNumerator` - Exposure
- `location.latitude` / `location.longitude` / `location.altitude` - GPS coordinates

### Attempted AI Fields (NOT AVAILABLE)
The following fields were explicitly requested but returned no data:
- `tags` - No tags/labels
- `caption` - No AI captions
- `labels` - No labels
- `faces` - No facial recognition data
- `objects` - No object detection
- `text` - No OCR text
- `insights` - No insights
- `aiMetadata` - No AI metadata
- `computerVision` - No vision analysis
- `searchableText` - No searchable text

### Analytics Field
The `analytics` field exists but returns null:
```json
"analytics": {
  "allTime": null,
  "lastSevenDays": null
}
```

### Thumbnails
The `thumbnails` field provides pre-generated thumbnail URLs in three sizes (small, medium, large) with dimensions and URLs, but **no AI analysis metadata**.

## Endpoints That Failed

- `/drives/{id}/items/{id}/thumbnails` - Returns "Invalid request" (400)
- `/drives/{id}/items/{id}/analytics` - Returns "API not found" (400)
- `/drives/{id}/root/search(q='...')` - Returns error (400)

## Conclusion

**No AI-generated metadata is currently available** through the Microsoft Graph API for OneDrive Personal accounts, even when using undocumented fields or the beta endpoint.

The only metadata available is:
1. EXIF data (already in image files)
2. OneDrive system metadata (upload dates, sharing info)
3. Thumbnail URLs (no analysis, just pre-rendered images)

## Microsoft's Future Plans

According to Microsoft's 2026 announcements, AI features are coming to OneDrive including:
- Facial recognition tagging
- Natural language search
- SharePoint Autofill for metadata extraction

However, these features are not yet exposed in the API as of January 2026.

## Recommendation

For this project, there is **no value in extracting additional metadata** from the OneDrive API. All useful metadata (EXIF data) is already embedded in the downloaded image files themselves.
