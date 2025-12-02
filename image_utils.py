from PIL import Image, ImageDraw, ImageFont, ImageFilter
import aiohttp
import io
from typing import Optional

async def create_stats_image(
    user,
    banner_url: Optional[str],
    avatar_url: str,
    username: str,
    join_date: Optional[str],
    has_nitro: bool = False,
    hypesquad_type: Optional[str] = None,
    badges: list = []
) -> io.BytesIO:
    width = 885
    height = 303
    
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    
    if banner_url:
        async with aiohttp.ClientSession() as session:
            async with session.get(banner_url) as resp:
                if resp.status == 200:
                    banner_data = await resp.read()
                    banner = Image.open(io.BytesIO(banner_data))
                    
                    aspect = banner.width / banner.height
                    target_aspect = width / height
                    
                    if aspect > target_aspect:
                        new_height = height
                        new_width = int(aspect * new_height)
                    else:
                        new_width = width
                        new_height = int(new_width / aspect)
                    
                    banner = banner.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    banner = banner.filter(ImageFilter.GaussianBlur(radius=10))
                    
                    x = (new_width - width) // 2
                    y = (new_height - height) // 2
                    banner = banner.crop((x, y, x + width, y + height))
                    
                    img.paste(banner, (0, 0))
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as resp:
                if resp.status == 200:
                    avatar_data = await resp.read()
                    avatar_bg = Image.open(io.BytesIO(avatar_data))
                    
                    aspect = avatar_bg.width / avatar_bg.height
                    target_aspect = width / height
                    
                    if aspect > target_aspect:
                        new_height = height
                        new_width = int(aspect * new_height)
                    else:
                        new_width = width
                        new_height = int(new_width / aspect)
                    
                    avatar_bg = avatar_bg.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    avatar_bg = avatar_bg.filter(ImageFilter.GaussianBlur(radius=15))
                    
                    x = (new_width - width) // 2
                    y = (new_height - height) // 2
                    avatar_bg = avatar_bg.crop((x, y, x + width, y + height))
                    
                    img.paste(avatar_bg, (0, 0))
    
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            if resp.status == 200:
                avatar_data = await resp.read()
                avatar = Image.open(io.BytesIO(avatar_data))
                avatar = avatar.resize((250, 250), Image.Resampling.LANCZOS)
                
                mask = Image.new('L', (250, 250), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 250, 250), fill=255)
                
                img.paste(avatar, (30, 26), mask)
    
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    username_bbox = draw.textbbox((0, 0), username, font=font_large)
    username_width = username_bbox[2] - username_bbox[0]
    
    avatar_right = 280
    left_margin = 25
    
    min_text_x_for_left = avatar_right + left_margin + (username_width / 2)
    center_x = width / 2
    
    text_x = max(center_x, min_text_x_for_left)
    
    draw.text((int(text_x), 120), username, fill=(255, 255, 255), font=font_large, anchor="mt")
    
    if join_date and join_date != 'N/A':
        if '<t:' in join_date:
            join_text = join_date.split(':')[1].split(':')[0]
            try:
                from datetime import datetime
                timestamp = int(join_text)
                dt = datetime.fromtimestamp(timestamp)
                join_text = f"{dt.strftime('%b %d, %Y')}"
            except (ValueError, IndexError):
                join_text = "N/A"
        else:
            join_text = join_date
        
        text_bbox = draw.textbbox((0, 0), join_text, font=font_small)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        padding = 15
        circle_x = width - text_width - padding * 2 - 20
        circle_y = height - text_height - padding * 2 - 20
        circle_width = text_width + padding * 2
        circle_height = text_height + padding * 2
        
        draw.rounded_rectangle(
            ((circle_x, circle_y), (circle_x + circle_width, circle_y + circle_height)),
            radius=20,
            fill=(40, 40, 40, 200)
        )
        
        text_x = circle_x + padding
        text_y = circle_y + padding
        draw.text((text_x, text_y), join_text, fill=(255, 255, 255), font=font_small)
    
    badge_y = 15
    badge_x = width - 20
    
    if hypesquad_type:
        print(f"[DEBUG] Hypesquad type detected: {hypesquad_type}")
        hypesquad_urls = {
            'balance': 'https://cdn.discordapp.com/badge-icons/3c6ccb21cb56820e4eaf0aed9d30f7da/hypesquad_balance.png',
            'brilliance': 'https://cdn.discordapp.com/badge-icons/9ef7e029c1da4f9505aff1e67791ee99/hypesquad_brilliance.png',
            'bravery': 'https://cdn.discordapp.com/badge-icons/8a88d63823ae4500da24bd7d1f4778b0/hypesquad_bravery.png'
        }
        
        badge_url = hypesquad_urls.get(hypesquad_type.lower())
        print(f"[DEBUG] Badge URL: {badge_url}")
        if badge_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(badge_url) as resp:
                        print(f"[DEBUG] Response status: {resp.status}")
                        if resp.status == 200:
                            badge_data = await resp.read()
                            print(f"[DEBUG] Badge data size: {len(badge_data)}")
                            badge_img = Image.open(io.BytesIO(badge_data)).convert('RGBA')
                            badge_img = badge_img.resize((45, 45), Image.Resampling.LANCZOS)
                            img.paste(badge_img, (width - 55, badge_y), badge_img)
                            print(f"[DEBUG] Badge pasted successfully")
                            badge_x -= 60
            except Exception as e:
                print(f"[ERROR] Error loading hypesquad badge: {e}")
                import traceback
                traceback.print_exc()
    
    if has_nitro:
        nitro_size = 35
        badge_x_pos = badge_x - nitro_size - 10
        badge_y_pos = badge_y
        
        draw.ellipse(
            [(badge_x_pos, badge_y_pos), (badge_x_pos + nitro_size, badge_y_pos + nitro_size)],
            fill=(127, 75, 200)
        )
        
        bbox = draw.textbbox((0, 0), "N", font=font_small)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = badge_x_pos + (nitro_size - text_w) // 2
        text_y = badge_y_pos + (nitro_size - text_h) // 2
        draw.text((text_x, text_y), "N", fill=(255, 255, 255), font=font_small)
    
    img_rgba = img.convert('RGBA')
    border_img = Image.new('RGBA', (width + 20, height + 20), (0, 0, 0, 80))
    border_img.paste(img_rgba, (10, 10))
    
    output = io.BytesIO()
    border_img.save(output, format='PNG')
    output.seek(0)
    return output
