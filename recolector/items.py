import scrapy

class RecursoItem(scrapy.Item):
    id = scrapy.Field()
    titulo = scrapy.Field()
    texto = scrapy.Field()
    autor = scrapy.Field()
    categorias = scrapy.Field()
    url = scrapy.Field()
    fuente = scrapy.Field()