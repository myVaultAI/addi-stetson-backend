# SVG Icon Library - Stetson Dashboard

**Created**: January 2025  
**Purpose**: Comprehensive icon library for RAG system and dashboard components  
**Location**: `/Users/jason/Projects/addi_demo/addi_backend/static/logos/`

---

## 🎯 Icon Library Overview

This library contains all SVG icons used in the Stetson Dashboard and can be expanded through the RAG system. Icons are organized by category and optimized for both light and dark themes.

---

## 📁 Icon Categories

### **Navigation Icons**
- `dashboard.svg` - Main dashboard icon
- `search.svg` - Search functionality
- `alerts.svg` - High priority alerts
- `notes.svg` - Notes/documentation
- `chat.svg` - New chat/conversation
- `settings.svg` - Settings/configuration
- `analytics.svg` - Analytics/reports
- `users.svg` - User management

### **Status Icons**
- `success.svg` - Success/complete status
- `warning.svg` - Warning/attention needed
- `error.svg` - Error/critical issues
- `info.svg` - Information/neutral
- `pending.svg` - Pending/in-progress
- `resolved.svg` - Resolved/completed

### **Communication Icons**
- `phone.svg` - Phone calls
- `email.svg` - Email communication
- `sms.svg` - Text messages
- `chat-bubble.svg` - Chat conversations
- `video-call.svg` - Video calls
- `escalation.svg` - Escalation alerts

### **Data Visualization Icons**
- `chart-line.svg` - Line charts
- `chart-bar.svg` - Bar charts
- `chart-pie.svg` - Pie charts
- `chart-donut.svg` - Donut charts
- `trending-up.svg` - Upward trends
- `trending-down.svg` - Downward trends
- `trending-neutral.svg` - Stable trends

### **Action Icons**
- `refresh.svg` - Refresh/reload
- `download.svg` - Download/export
- `upload.svg` - Upload/import
- `edit.svg` - Edit/modify
- `delete.svg` - Delete/remove
- `add.svg` - Add/create new
- `filter.svg` - Filter/search
- `sort.svg` - Sort/order

### **Academic Icons**
- `graduation-cap.svg` - Graduation/degree
- `book.svg` - Education/learning
- `notebook.svg` - Notes/study
- `pencil.svg` - Writing/editing
- `calculator.svg` - Math/finance
- `calendar.svg` - Scheduling/events
- `clock.svg` - Time/duration
- `location.svg` - Campus/location

---

## 🎨 Icon Specifications

### **Standard Sizes**
- **Small**: 16x16px (`icon-sm`)
- **Medium**: 20x20px (`icon`)
- **Large**: 24x24px (`icon-lg`)
- **Extra Large**: 32x32px (`icon-xl`)

### **Color Variants**
- **Light Theme**: `#1E293B` (dark text on light background)
- **Dark Theme**: `#F1F5F9` (light text on dark background)
- **Primary**: `#006838` (Stetson green)
- **Accent**: `#A3A954` (Stetson gold)
- **Success**: `#10B981` (green)
- **Warning**: `#F59E0B` (orange)
- **Error**: `#EF4444` (red)
- **Info**: `#3B82F6` (blue)

### **Stroke Properties**
- **Width**: 2px (standard), 1.5px (small), 2.5px (large)
- **Line Cap**: `round`
- **Line Join**: `round`
- **Fill**: `none` (outline style)

---

## 📝 Icon Usage Examples

### **React Component Usage**
```typescript
import { Icon } from '@/components/atoms/Icon'

// Basic usage
<Icon name="dashboard" size="lg" color="primary" />

// With custom styling
<Icon 
  name="escalation" 
  size="sm" 
  color="error" 
  className="animate-pulse" 
/>
```

### **CSS Class Usage**
```css
.icon-dashboard {
  background-image: url('/static/logos/dashboard.svg');
  background-size: 20px 20px;
  background-repeat: no-repeat;
}
```

### **SVG Inline Usage**
```html
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
  <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"/>
</svg>
```

---

## 🔧 Icon Management System

### **Adding New Icons**
1. Create SVG file in appropriate category folder
2. Follow naming convention: `kebab-case.svg`
3. Update this documentation
4. Add to RAG system for future reference
5. Test in both light and dark themes

### **Icon Naming Convention**
- Use descriptive, action-based names
- Use kebab-case (lowercase with hyphens)
- Include size/type suffix if needed: `chart-line-large.svg`
- Group related icons: `chart-*`, `status-*`, `action-*`

### **Quality Standards**
- ✅ Optimized SVG (minimal markup)
- ✅ Consistent viewBox (24x24 recommended)
- ✅ Proper stroke width (2px standard)
- ✅ Accessible (proper ARIA labels)
- ✅ Theme compatible (works in light/dark)
- ✅ Scalable (vector-based)

---

## 📊 Current Icon Inventory

| Category | Count | Status |
|----------|-------|--------|
| Navigation | 8 | ✅ Complete |
| Status | 6 | ✅ Complete |
| Communication | 6 | ✅ Complete |
| Data Visualization | 7 | ✅ Complete |
| Action | 8 | ✅ Complete |
| Academic | 8 | ✅ Complete |
| **Total** | **43** | **✅ Complete** |

---

## 🚀 Future Expansion

### **Planned Additions**
- **Social Media Icons**: Twitter, Facebook, Instagram, LinkedIn
- **File Type Icons**: PDF, DOC, XLS, PPT, ZIP
- **Device Icons**: Desktop, Mobile, Tablet, Smartwatch
- **Weather Icons**: Sun, Cloud, Rain, Snow (for campus events)
- **Sports Icons**: Football, Basketball, Soccer (for athletics)

### **RAG Integration**
Icons are automatically indexed in the RAG system for easy discovery:
- Search: "notebook icon" → Returns notebook.svg
- Search: "chart visualization" → Returns all chart icons
- Search: "status indicators" → Returns all status icons

---

## 🎓 Stetson Branding

All icons maintain Stetson University branding:
- **Primary Color**: Stetson Green (#006838)
- **Accent Color**: Stetson Gold (#A3A954)
- **Style**: Clean, professional, academic
- **Accessibility**: WCAG 2.1 AA compliant
- **Consistency**: Unified design language

---

**Last Updated**: January 2025  
**Maintained By**: Addi Dashboard Team  
**Version**: 1.0.0

---

*This icon library supports the Stetson University Addi Dashboard and can be expanded through the RAG system as new icons are needed.*
