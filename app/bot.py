import asyncio
import math
import random
import logging
import traceback
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from gtts import gTTS
from playwright.async_api import async_playwright, TimeoutError

logger = logging.getLogger('TutorGebraBot')

import concurrent.futures

def _generate_single_audio(step, lang):
    cmd = step["command"]
    text = step["speech"]
    if not text:
        return
    safe_name = "".join(c if c.isalnum() else "_" for c in cmd)[:50]
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audios", f"{safe_name}.mp3")
    if not os.path.exists(filepath):
        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(filepath)
        except Exception as e:
            logger.error(f"Error generating audio for '{cmd}': {e}")

def pregenerate_audio(steps, lang="en"):
    logger.info("Synthesizing teacher voice with gTTS in parallel...")
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "audios"), exist_ok=True)
    pygame.mixer.init()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, max(1, len(steps)))) as executor:
        futures = [executor.submit(_generate_single_audio, step, lang) for step in steps]
        concurrent.futures.wait(futures)
        
    logger.info("Audios ready.")

def play_audio(cmd):
    safe_name = "".join(c if c.isalnum() else "_" for c in cmd)[:50]
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audios", f"{safe_name}.mp3")
    if os.path.exists(filepath):
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")

class HumanSimulator:
    def __init__(self, page):
        self.page = page
        self.mouse = page.mouse
        self.current_x = 0
        self.current_y = 0

    async def init_mouse(self):
        self.current_x = random.randint(200, 800)
        self.current_y = random.randint(200, 600)
        await self.mouse.move(self.current_x, self.current_y)

    def cubic_bezier(self, t, p0, p1, p2, p3):
        return (
            (1 - t)**3 * p0 +
            3 * (1 - t)**2 * t * p1 +
            3 * (1 - t) * t**2 * p2 +
            t**3 * p3
        )

    async def move_mouse(self, target_x, target_y):
        overshoot = random.random() < 0.4
        actual_target_x = target_x
        actual_target_y = target_y

        if overshoot:
            dx = target_x - self.current_x
            dy = target_y - self.current_y
            dist = math.hypot(dx, dy)
            if dist > 0:
                actual_target_x += (dx / dist) * random.randint(10, 30)
                actual_target_y += (dy / dist) * random.randint(10, 30)

        p0_x, p0_y = self.current_x, self.current_y
        p3_x, p3_y = actual_target_x, actual_target_y

        offset_x = random.randint(30, 150) * random.choice([1, -1])
        offset_y = random.randint(30, 150) * random.choice([1, -1])
        
        p1_x = p0_x + (p3_x - p0_x) * 0.3 + offset_x
        p1_y = p0_y + (p3_y - p0_y) * 0.3 - offset_y

        p2_x = p0_x + (p3_x - p0_x) * 0.7 - offset_x
        p2_y = p0_y + (p3_y - p0_y) * 0.7 + offset_y

        dist = math.hypot(p3_x - p0_x, p3_y - p0_y)
        steps = max(20, min(100, int(dist / 10))) 
        
        for i in range(steps + 1):
            t = i / steps
            x = self.cubic_bezier(t, p0_x, p1_x, p2_x, p3_x)
            y = self.cubic_bezier(t, p0_y, p1_y, p2_y, p3_y)
            
            await self.mouse.move(x, y)
            self.current_x = x
            self.current_y = y
            
            if t < 0.2 or t > 0.8:
                await asyncio.sleep(random.uniform(0.005, 0.015)) 
            else:
                await asyncio.sleep(random.uniform(0.001, 0.005)) 

        if overshoot:
            await asyncio.sleep(random.uniform(0.1, 0.3))
            steps_correct = random.randint(10, 20)
            for i in range(steps_correct + 1):
                t = i / steps_correct
                x = self.current_x + (target_x - self.current_x) * t
                y = self.current_y + (target_y - self.current_y) * t
                await self.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.005, 0.01))
            self.current_x = target_x
            self.current_y = target_y

    async def click(self):
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await self.mouse.down()
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await self.mouse.up()

    async def type_text(self, text):
        in_quotes = False
        clean_text = ""
        for char in text:
            if char == '"':
                in_quotes = not in_quotes
            if char == ' ' and not in_quotes:
                continue
            clean_text += char
            
        for char in clean_text:
            await self.page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.02, 0.08))
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.1, 0.3))
        
        await asyncio.sleep(random.uniform(0.1, 0.4))
        await self.page.keyboard.press("Enter", delay=150)

    async def cognitive_pause(self, min_s=0.5, max_s=2.0):
        await asyncio.sleep(random.uniform(min_s, max_s))


async def run_geogebra_session(data):
    steps = data.get("steps", [])
    lang = data.get("language", "en")
    pregenerate_audio(steps, lang)

    try:
        async with async_playwright() as p:
            logger.info("Starting Chromium browser...")
            browser = await p.chromium.launch(headless=False, slow_mo=30, args=['--start-maximized'])
            
            context = await browser.new_context(
                no_viewport=True
            )
            page = await context.new_page()
            
            page.on("console", lambda msg: logger.warning(f"GeoGebra Console: {msg.text}") if msg.type == "error" else None)
            
            sim = HumanSimulator(page)
            
            logger.info("Opening GeoGebra Classic...")
            try:
                await page.bring_to_front()
                await page.goto("https://www.geogebra.org/classic", timeout=60000)
                await page.wait_for_load_state("networkidle")
            except TimeoutError:
                logger.warning("Slow network. Continuing...")
                
            logger.info("Waiting for stabilization...")
            await asyncio.sleep(6)
            await sim.init_mouse()

            logger.info("Searching for input bar...")
            try:
                await page.wait_for_selector(".avInput", timeout=5000)
                elements = await page.query_selector_all(".avInput")
                if elements:
                    box = await elements[0].bounding_box()
                    if box:
                        await sim.move_mouse(box['x'] + 50, box['y'] + box['height'] / 2)
                        await sim.click()
            except Exception:
                await sim.move_mouse(80, 80)
                await sim.click()
                await sim.cognitive_pause(0.5, 1.0)
                await sim.click()
            
            logger.info(f"Starting {len(steps)} commands...")
            for i, step in enumerate(steps):
                cmd = step["command"]
                speech = step["speech"]
                logger.info(f"[{i+1}/{len(steps)}] Command: {cmd}")
                
                if speech:
                    play_audio(cmd)
                
                if random.random() < 0.3:
                    idle_x = sim.current_x + random.randint(-100, 100)
                    idle_y = sim.current_y + random.randint(-100, 100)
                    await sim.move_mouse(max(10, min(1300, idle_x)), max(10, min(750, idle_y)))
                
                await sim.cognitive_pause(0.5, 1.5)
                await sim.type_text(cmd)
                
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.5)
                    
                await asyncio.sleep(1.0)

            logger.info("Lesson finished.")
            
            await sim.cognitive_pause(1.0, 3.0)
            await sim.move_mouse(600, 300)
            
            # Dejamos el navegador abierto unos minutos para que el estudiante revise
            await asyncio.sleep(300)
            await browser.close()
    finally:
        try:
            pygame.mixer.quit()
            import shutil
            shutil.rmtree(os.path.join(os.path.dirname(os.path.dirname(__file__)), "audios"), ignore_errors=True)
            logger.info("Final cleanup guaranteed: Audios deleted from disk.")
        except Exception as e:
            logger.warning(f"Could not clean up audios: {e}")