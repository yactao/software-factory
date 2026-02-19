import sys
from pathlib import Path

# =========================
# Fix PYTHON PATH
# =========================
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json
import math
from modules.vision_analysis import VisionAnalyzer


class PlanAnnotator:
    def __init__(self, master):
        self.master = master
        self.master.title("Plan Annotator Pro")

        # --- Canvas ---
        self.canvas = tk.Canvas(master, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # --- Barre de boutons ---
        btn_frame = tk.Frame(master)
        btn_frame.pack(side=tk.TOP, fill=tk.X)
        buttons = [
            ("Ouvrir Plan", self.load_image),
            ("Détection Auto", self.detect_objects),
            ("Rect", lambda: self.set_mode("rect")),
            ("Polygone", lambda: self.set_mode("polygon")),
            ("Point", lambda: self.set_mode("point")),
            ("Mesure", lambda: self.set_mode("measure")),
            ("Nommer", lambda: self.set_mode("label")),
            ("Modifier Box", self.edit_box),
            ("Supprimer Box", self.delete_box),
            ("Annuler", self.undo),
            ("Exporter JSON", self.export_json)
        ]
        for text, cmd in buttons:
            tk.Button(btn_frame, text=text, command=cmd).pack(side=tk.LEFT)

        # --- Variables ---
        self.image = None
        self.tk_image = None
        self.mode = None
        self.start_pos = None
        self.current_rect = None
        self.current_polygon = []
        self.annotations = []
        self.measure_start = None
        self.selected_annotation = None  # Pour édition
        self.edit_mode = None  # 'move' ou 'resize'
        self.selected_corner = None  # Coin sélectionné pour resize

        # --- Bindings ---
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # --- VisionAnalyzer ---
        CV_ENDPOINT = "https://visionarchi01-prediction.cognitiveservices.azure.com/"
        CV_PRED_KEY = "92J5mHjhhG3DRK4NnOStMiAFAgc80UcnLuuOBYFHihcDzA1EGitqJQQJ99BIACYeBjFXJ3w3AAAIACOGwUfS"
        CV_PROJECT_ID = "2585564a-9630-43c3-8633-f35fc0d1fccf"
        CV_PUBLISHED_NAME = "Iteration5"
        self.vision_client = VisionAnalyzer(
            endpoint=CV_ENDPOINT,
            prediction_key=CV_PRED_KEY,
            model_name=CV_PUBLISHED_NAME,
            project_id=CV_PROJECT_ID
        )

    # =========================
    # Mode
    # =========================
    def set_mode(self, mode):
        self.mode = mode
        self.start_pos = None
        self.current_rect = None
        self.current_polygon = []
        self.measure_start = None
        self.selected_annotation = None
        self.edit_mode = None
        self.selected_corner = None
        print(f"Mode activé : {mode}")

    # =========================
    # Modifier Box
    # =========================
    def edit_box(self):
        self.set_mode("edit")
        print("Mode édition activé : clique sur une box pour la déplacer ou redimensionner")

    # =========================
    # Supprimer Box
    # =========================
    def delete_box(self):
        self.set_mode("delete")
        print("Mode suppression activé : clique sur une box pour la supprimer")

    # =========================
    # Chargement du plan
    # =========================
    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if not file_path:
            return
        self.image = Image.open(file_path)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

    # =========================
    # Détection Auto
    # =========================
    def detect_objects(self):
        if not self.image:
            messagebox.showwarning("Attention", "Ouvre d'abord un plan.")
            return

        detections = self.vision_client.detect_objects_pil(self.image)
        w, h = self.image.size

        for det in detections:
            bb = det["bounding_box"]
            left = bb["left"] * w
            top = bb["top"] * h
            width = bb["width"] * w
            height = bb["height"] * h

            rect_id = self.canvas.create_rectangle(
                left, top, left + width, top + height,
                outline="red", width=2
            )
            self.annotations.append({
                "id": rect_id,
                "type": "rect",
                "left": left,
                "top": top,
                "width": width,
                "height": height,
                "label": det["tag_name"],
                "surface": width*height,
                "perimeter": 2*(width+height)
            })

        messagebox.showinfo("Détection Auto", f"{len(detections)} objets détectés et annotés.")

    # =========================
    # Export JSON
    # =========================
    def export_json(self):
        if not self.annotations:
            messagebox.showinfo("Info", "Aucune annotation à exporter.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
        if not file_path:
            return
        with open(file_path, "w") as f:
            json.dump(self.annotations, f, indent=4)
        messagebox.showinfo("Export", f"{len(self.annotations)} annotations exportées.")

    # =========================
    # Annuler dernière annotation
    # =========================
    def undo(self):
        if not self.annotations:
            return
        last = self.annotations.pop()
        self.canvas.delete(last["id"])
        print("Dernière annotation supprimée")

    # =========================
    # Gestion clic / drag
    # =========================
    def on_click(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        if self.mode == "rect":
            self.start_pos = (x, y)
            self.current_rect = self.canvas.create_rectangle(x, y, x, y, outline="red", width=2)

        elif self.mode == "polygon":
            if self.current_polygon and self.is_close_to_first_point(x, y):
                polygon_id = self.canvas.create_polygon(self.current_polygon, outline="blue", fill='', width=2)
                surface = self.polygon_area(self.current_polygon)
                perimeter = self.polygon_perimeter(self.current_polygon)
                label = simple_input_dialog("Nom du polygone:")
                self.annotations.append({
                    "id": polygon_id,
                    "type": "polygon",
                    "points": self.current_polygon.copy(),
                    "label": label,
                    "surface": surface,
                    "perimeter": perimeter
                })
                self.current_polygon = []
            else:
                self.current_polygon.append((x, y))
                if len(self.current_polygon) > 1:
                    self.canvas.create_line(self.current_polygon[-2], self.current_polygon[-1], fill="blue", width=2)
                self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="blue")

        elif self.mode == "point":
            label = simple_input_dialog("Nom du point:")
            point_id = self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="green")
            self.annotations.append({"id": point_id, "type": "point", "x": x, "y": y, "label": label})

        elif self.mode == "measure":
            if not self.measure_start:
                self.measure_start = (x, y)
            else:
                x0, y0 = self.measure_start
                line_id = self.canvas.create_line(x0, y0, x, y, fill="orange", width=2)
                distance = math.hypot(x - x0, y - y0)
                self.canvas.create_text((x0+x)/2, (y0+y)/2, text=f"{distance:.1f}px", fill="orange")
                self.measure_start = None

        elif self.mode == "label":
            label = simple_input_dialog("Texte du label:")
            text_id = self.canvas.create_text(x, y, text=label, fill="purple", font=("Arial", 12))
            self.annotations.append({"id": text_id, "type": "label", "x": x, "y": y, "label": label})

        elif self.mode == "edit":
            self.selected_annotation = None
            corner_tol = 6
            for ann in self.annotations:
                if ann["type"] == "rect":
                    x0, y0 = ann["left"], ann["top"]
                    x1, y1 = x0 + ann["width"], y0 + ann["height"]

                    # Vérifier coins
                    corners = {"tl": (x0, y0), "tr": (x1, y0), "bl": (x0, y1), "br": (x1, y1)}
                    clicked_on_corner = False
                    for corner_name, (cx, cy) in corners.items():
                        if abs(x - cx) <= corner_tol and abs(y - cy) <= corner_tol:
                            self.edit_mode = "resize"
                            self.selected_corner = corner_name
                            self.selected_annotation = ann
                            clicked_on_corner = True
                            break
                    if clicked_on_corner:
                        break

                    # Si pas sur un coin mais à l'intérieur => déplacer
                    if x0 <= x <= x1 and y0 <= y <= y1:
                        self.edit_mode = "move"
                        self.selected_annotation = ann
                        self.start_pos = (x, y)
                        break

        elif self.mode == "delete":
            for ann in self.annotations:
                if ann["type"] == "rect":
                    x0, y0 = ann["left"], ann["top"]
                    x1, y1 = x0 + ann["width"], y0 + ann["height"]
                    if x0 <= x <= x1 and y0 <= y <= y1:
                        self.canvas.delete(ann["id"])
                        self.annotations.remove(ann)
                        print(f"Box '{ann['label']}' supprimée")
                        break

    def on_drag(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        if self.mode == "rect" and self.current_rect:
            x0, y0 = self.start_pos
            self.canvas.coords(self.current_rect, x0, y0, x, y)

        elif self.mode == "edit" and self.selected_annotation:
            ann = self.selected_annotation
            if self.edit_mode == "move":
                dx = x - self.start_pos[0]
                dy = y - self.start_pos[1]
                self.start_pos = (x, y)
                self.canvas.move(ann["id"], dx, dy)
                ann["left"] += dx
                ann["top"] += dy

            elif self.edit_mode == "resize":
                x0, y0 = ann["left"], ann["top"]
                w, h = ann["width"], ann["height"]
                x1, y1 = x0 + w, y0 + h

                if self.selected_corner == "tl":
                    x0_new, y0_new = x, y
                    ann["width"] = x1 - x0_new
                    ann["height"] = y1 - y0_new
                    ann["left"], ann["top"] = x0_new, y0_new
                elif self.selected_corner == "tr":
                    x1_new, y0_new = x, y
                    ann["width"] = x1_new - x0
                    ann["height"] = y1 - y0_new
                    ann["top"] = y0_new
                elif self.selected_corner == "bl":
                    x0_new, y1_new = x, y
                    ann["width"] = x1 - x0_new
                    ann["height"] = y1_new - y0
                    ann["left"] = x0_new
                elif self.selected_corner == "br":
                    x1_new, y1_new = x, y
                    ann["width"] = x1_new - x0
                    ann["height"] = y1 - y0

                # Mettre à jour coords canvas
                self.canvas.coords(ann["id"], ann["left"], ann["top"], ann["left"]+ann["width"], ann["top"]+ann["height"])

    def on_release(self, event):
        if self.mode == "rect" and self.current_rect:
            x0, y0 = self.start_pos
            x1, y1 = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            width = abs(x1 - x0)
            height = abs(y1 - y0)
            label = simple_input_dialog("Nom du rectangle:")
            self.annotations.append({
                "id": self.current_rect,
                "type": "rect",
                "left": min(x0, x1),
                "top": min(y0, y1),
                "width": width,
                "height": height,
                "label": label,
                "surface": width*height,
                "perimeter": 2*(width+height)
            })
            self.current_rect = None
            self.start_pos = None

        elif self.mode == "edit" and self.selected_annotation:
            print(f"Edition terminée : {self.selected_annotation['label']}")
            self.selected_annotation = None
            self.edit_mode = None
            self.selected_corner = None

    # =========================
    # Polygone utils
    # =========================
    def is_close_to_first_point(self, x, y, tol=10):
        if not self.current_polygon:
            return False
        x0, y0 = self.current_polygon[0]
        return (x - x0)**2 + (y - y0)**2 <= tol**2

    def polygon_area(self, points):
        n = len(points)
        if n < 3: return 0
        area = 0
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i+1)%n]
            area += x0*y1 - x1*y0
        return abs(area)/2

    def polygon_perimeter(self, points):
        n = len(points)
        peri = 0
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i+1)%n]
            peri += math.hypot(x1 - x0, y1 - y0)
        return peri


# =========================
# Dialog simple pour label
# =========================
def simple_input_dialog(prompt):
    dialog = tk.Toplevel()
    dialog.title("Entrer valeur")
    tk.Label(dialog, text=prompt).pack(padx=10, pady=10)
    entry = tk.Entry(dialog)
    entry.pack(padx=10, pady=10)
    result = []
    def on_ok():
        result.append(entry.get())
        dialog.destroy()
    tk.Button(dialog, text="OK", command=on_ok).pack(pady=10)
    dialog.grab_set()
    dialog.wait_window()
    return result[0] if result else "Objet"


# =========================
# Lancer l'application
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    app = PlanAnnotator(root)
    root.mainloop()
