import os
import random
from PIL import Image, ImageDraw, ImageFont
import io
from typing import Tuple
import logging

logger = logging.getLogger('captcha_bot')


class ImageGenerator:
    def __init__(self):
        self.raven_patterns = {
            'raven0.gif': 5, 'raven1.gif': 3, 'raven2.gif': 4,
            'raven3.gif': 1, 'raven4.gif': 6, 'raven5.gif': 5,
            'raven6.gif': 5, 'raven7.gif': 4, 'raven8.gif': 8,
            'raven9.gif': 5, 'raven10.gif': 1, 'raven11.gif': 3,
            'raven12.gif': 2, 'raven13.gif': 1, 'raven14.gif': 7,
            'raven15.gif': 2, 'raven16.gif': 7, 'raven17.gif': 4,
            'raven18.gif': 3, 'raven19.gif': 1, 'raven20.gif': 8,
            'raven21.gif': 7, 'raven22.gif': 5, 'raven23.gif': 1,
            'raven24.gif': 5
        }

    def generate_math_problem(self) -> Tuple[str, str, int]:
        pattern_file = random.choice(list(self.raven_patterns.keys()))
        pattern_answer = self.raven_patterns[pattern_file]

        # Generate polynomial coefficients
        coefficients = [random.randint(0, 20) for _ in range(random.randint(3, 4))]

        # Create polynomial expression
        terms = []
        for i, coef in enumerate(reversed(coefficients)):
            if coef != 0:
                if i == 0:
                    terms.append(str(coef))
                elif i == 1:
                    terms.append(f"{coef}x")
                else:
                    terms.append(f"{coef}x^{i}")
        polynomial = " + ".join(reversed(terms))

        # Calculate derivatives and final answer
        derivative_order = random.randint(1, 3)
        current_coefficients = coefficients.copy()

        for _ in range(derivative_order):
            current_coefficients = [
                coef * (i + 1)
                for i, coef in enumerate(current_coefficients[1:], 0)
            ]

        x = pattern_answer
        result = sum(coef * (x ** i) for i, coef in enumerate(current_coefficients)) + x

        problem_text = (
            f"Let x be the correct pattern\n"
            f"f(x) = {polynomial}\n"
            f"What is f{''.join(['\'' for _ in range(derivative_order)])}(x) + x?"
        )

        return pattern_file, problem_text, result

    def generate_background_text(self) -> str:
        """Generate random mathematical-looking text for background."""
        chars = "0123456789+-*/()=xf'"
        text = ""
        for _ in range(5):  # Number of terms
            term_length = random.randint(3, 8)
            text += ''.join(random.choice(chars) for _ in range(term_length)) + " "
        return text

    async def create_problem_image(self, pattern_file: str, problem_text: str) -> io.BytesIO:
        try:
            try:
                question_font = ImageFont.truetype('Arial', 16)
                noise_font = ImageFont.truetype('Arial', 64)
            except:
                question_font = ImageFont.load_default()
                noise_font = ImageFont.load_default()

            pattern_image = Image.open(os.path.join('img', pattern_file))
            pattern_image = pattern_image.convert('RGB')
            pattern_image = pattern_image.resize((360, 360))

            combined_image = Image.new('RGB', (360, 460), 'white')
            combined_image.paste(pattern_image, (0, 0))

            combined_image = combined_image.convert('RGBA')
            draw = ImageDraw.Draw(combined_image)

            chars = ''.join(chr(i) for i in range(32, 127))
            for _ in range(50):
                x = random.randint(0, combined_image.width - 1)
                y = random.randint(0, combined_image.height - 1)

                noise_text = random.choice(chars)
                if random.random() < 0.3:
                    noise_text += random.choice(chars)

                noise_layer = Image.new('RGBA', combined_image.size, (255, 255, 255, 0))
                noise_draw = ImageDraw.Draw(noise_layer)

                noise_draw.text(
                    (x, y),
                    noise_text,
                    fill=(200, 80, 0, 90),  # RGBA with alpha for opacity
                    font=noise_font
                )
                combined_image = Image.alpha_composite(combined_image, noise_layer)

            lines = problem_text.split('\n')
            for i, line in enumerate(lines):
                y_pos = 380 + (i * 25)
                for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                    draw.text(
                        (10 + dx, y_pos + dy),
                        line,
                        fill='black',
                        font=question_font
                    )

            buffer = io.BytesIO()
            combined_image.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer
        except Exception as e:
            logger.error(f'Error creating problem image: {str(e)}')
            raise