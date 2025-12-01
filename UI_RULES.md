# UI Design Rules - Efootball Team Builder

## Nguyên tắc tổng quát
- **Mục tiêu**: UI chuyên nghiệp, tối giản, không trông "AI quá"
- **Philosophy**: Less is more - Tập trung vào content, không làm phân tâm

---

## 1. COLOR PALETTE

### Primary Colors
- **Background**: Neutral dark (#1a1a1a, #252525)
- **Surface/Card**: Neutral (#2a2a2a, #323232)
- **Border**: Neutral light (#3a3a3a, #404040) - Dùng border thay vì shadow

### Text Colors
- **Primary Text**: Neutral light (#e5e5e5, #f5f5f5)
- **Secondary Text**: Neutral medium (#a0a0a0, #b0b0b0)
- **Muted Text**: Neutral dark (#707070, #808080)

### Accent Colors
- **Primary Accent**: Warm accent (không dùng xanh/tím AI) - Ví dụ: #f59e0b (amber), #ef4444 (red)
- **Success**: Green (#22c55e)
- **Warning**: Orange (#f59e0b)
- **Error**: Red (#ef4444)
- **Info**: Blue nhạt (#3b82f6) - chỉ dùng khi cần

### Tránh
- ❌ Màu xanh-tím phổ biến của AI (#3b82f6, #8b5cf6)
- ❌ Gradient tràn lan
- ❌ Màu quá sáng, chói

---

## 2. TYPOGRAPHY

### Font Family
- **Heading**: Montserrat, system-ui, sans-serif (font-weight: 600)
- **Body**: 'Be Vietnam Pro', 'Inter', system-ui, sans-serif (font-weight: 400/500)
- **Code/Mono**: 'JetBrains Mono', 'Fira Code', monospace

### Font Sizes
- **H1 (Title)**: 32px (2rem)
- **H2 (Header)**: 24px (1.5rem)
- **H3 (Subheader)**: 20px (1.25rem)
- **H4**: 18px (1.125rem)
- **Body**: 16px (1rem)
- **Small/Caption**: 14px (0.875rem)
- **Tiny**: 12px (0.75rem)

### Font Weights
- **Heading**: 600 (semibold)
- **Body**: 400 (regular) / 500 (medium)
- **Bold**: 700 (chỉ dùng khi cần nhấn mạnh)

---

## 3. SPACING SYSTEM

### Scale
- **Base unit**: 4px
- **Scale**: 4, 8, 12, 16, 20, 24, 32, 48, 64

### Spacing Rules
- **Page padding**: 24px (desktop), 16px (mobile)
- **Section spacing**: 48px (giữa các section lớn)
- **Card padding**: 24px (card lớn), 16px (card nhỏ)
- **Element spacing**: 16px (giữa các element trong card)
- **Item spacing**: 12px (giữa các item trong list)
- **Tight spacing**: 8px (giữa label và input)

### Grid
- **Column gap**: 24px
- **Row gap**: 24px

---

## 4. BORDERS & RADIUS

### Border
- **Width**: 1px solid
- **Color**: border-neutral (#3a3a3a)
- **NO box-shadow** - Dùng border thay thế

### Border Radius
- **Large card/section**: 16px (rounded-xl)
- **Medium card**: 12px (rounded-lg)
- **Small card/button**: 8px (rounded-md)
- **Input/field**: 6px (rounded)
- **Badge/tag**: 4px (rounded-sm)

### Rules
- ❌ Không dùng border-radius quá đà
- ✅ Rounded cha phải lớn hơn rounded con
- ✅ Nhất quán trong toàn bộ app

---

## 5. COMPONENTS

### Buttons
- **Padding**: 12px 24px
- **Border-radius**: 8px
- **Font-size**: 16px
- **Border**: 1px solid (không shadow)
- **Hover**: Background thay đổi nhẹ, không có animation lố

### Cards
- **Background**: Surface color (#2a2a2a)
- **Border**: 1px solid border color
- **Padding**: 24px (large), 16px (medium)
- **Border-radius**: 12px (medium card)
- **NO shadow** - chỉ dùng border

### Input Fields
- **Border**: 1px solid
- **Border-radius**: 6px
- **Padding**: 10px 12px
- **Background**: Dark background

### Badges/Tags
- **Padding**: 4px 12px
- **Border-radius**: 4px
- **Font-size**: 14px
- **Border**: 1px solid

---

## 6. ICONS & EMOJIS

### Icons
- ✅ **Sử dụng**: Text labels hoặc icon library (nếu cần)
- ❌ **Không dùng**: Emoji trong UI chính
- ✅ **Khi cần icon**: Dùng Unicode symbols hoặc text ngắn gọn

### Labels
- **Thay vì emoji**: Dùng text ngắn gọn, rõ ràng
- Ví dụ:
  - "Tổng quan" thay vì "📊 Tổng quan"
  - "Cầu thủ" thay vì "⚽ Cầu thủ"
  - "Thêm mới" thay vì "➕ Thêm mới"

---

## 7. ANIMATIONS

### Rules
- ❌ Không animation lố, loạn
- ✅ Animation mượt, tối giản
- ✅ Chỉ animation khi thật sự cần (hover, transition)
- ✅ Duration: 200-300ms
- ✅ Easing: ease-in-out

### Allowed
- Fade in/out: 200ms
- Smooth hover: 200ms
- Page transition: 300ms

### Prohibited
- ❌ Bounce, shake, rotate
- ❌ Animation quá nhanh/chậm
- ❌ Nhiều animation cùng lúc

---

## 8. GLASSMORPHISM & EFFECTS

### Tránh
- ❌ Glassmorphism/blur background
- ❌ Gradient backgrounds
- ❌ Shadow effects
- ❌ Glow effects

### Dùng
- ✅ Solid colors
- ✅ Simple borders
- ✅ Clean, flat design

---

## 9. LAYOUT

### Structure
- **Max width**: 1400px (nếu cần)
- **Content padding**: 24px
- **Sidebar width**: 280px (Streamlit default)

### Sections
- **Margin bottom**: 48px (giữa sections lớn)
- **Margin bottom**: 32px (giữa subsections)

---

## 10. SPECIFIC STREAMLIT COMPONENTS

### Headers
- **H1**: 32px, weight 600, color primary text
- **H2**: 24px, weight 600, color primary text
- **H3**: 20px, weight 600, color primary text

### Metrics
- **Number**: 32px, weight 600
- **Label**: 14px, color secondary text

### Tables/Dataframes
- **Border**: 1px solid border color
- **Row hover**: Background thay đổi nhẹ
- **Header**: Background surface, text primary

### Success/Error/Warning Messages
- **Border**: 1px solid
- **Background**: Subtle background
- **Padding**: 16px
- **Border-radius**: 8px

---

## 11. RESPONSIVE DESIGN

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Rules
- Spacing giảm 25% trên mobile
- Font size giảm 10% trên mobile
- Padding giảm trên mobile

---

## 12. ACCESSIBILITY

### Contrast
- Text phải có contrast ratio >= 4.5:1
- Focus states rõ ràng

### Touch Targets
- Minimum 44x44px cho mobile

---

## NOTES

1. **Consistency is key**: Áp dụng rules này nhất quán trong toàn bộ app
2. **Less is more**: Khi nghi ngờ, chọn option đơn giản hơn
3. **Content first**: UI phục vụ content, không làm phân tâm
4. **Professional**: Tránh mọi thứ trông "AI quá"

---

## CHANGELOG

- 2024: Initial rules - Focus on professional, minimal design

