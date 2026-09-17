import hashlib
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

class RecursoPipeline:
    def process_item(self, item, spider=None):
        a = ItemAdapter(item)
        a["texto"] = " ".join(a.get("texto", "").split())
        if not a["texto"] or not a.get("url"):
            raise DropItem("Falta texto o URL")
        clave = a["url"] + "|" + a["texto"]
        a["id"] = hashlib.sha256(clave.encode()).hexdigest()
        return item