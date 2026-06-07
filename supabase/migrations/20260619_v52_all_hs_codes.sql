-- V52: Complete HS code reference (all 97 chapters)
-- Source: UN COMTRADE, OEC World, Trading Economics, WCO

-- Insert remaining HS chapters not covered in V50
INSERT INTO hs_code_reference (hs_chapter, hs_section, description_uz, description_en, description_ru, typical_vat_pct, typical_freight_factor_pct, uzb_local_production, has_import_substitution)
SELECT * FROM (VALUES
    -- Section I - Live Animals; Animal Products
    ('01', 'I', 'Tirik hayvonlar', 'Live animals', 'Живые животные', 12, 25, true, false),
    ('02', 'I', 'Go''sht va qo''yim mahsulotlari', 'Meat and edible meat offal', 'Мясо и субпродукты', 12, 25, true, true),
    ('03', 'I', 'Baliq va qisqichbaqasimonlar', 'Fish and crustaceans', 'Рыба и ракообразные', 12, 30, false, false),
    ('04', 'I', 'Sut mahsulotlari, tuxum, asal', 'Dairy, eggs, honey', 'Молочные продукты, яйца, мед', 12, 25, true, true),
    ('05', 'I', 'Hayvonot mahsulotlari', 'Products of animal origin', 'Продукты животного происхождения', 12, 25, true, false),
    -- Section II - Vegetable Products
    ('06', 'II', 'Tirik daraxtlar va o''simliklar', 'Live trees and plants', 'Живые деревья и растения', 12, 30, true, false),
    ('07', 'II', 'Sabzavotlar', 'Edible vegetables', 'Овощи', 12, 30, true, true),
    ('08', 'II', 'Yeyiladigan mevalar', 'Edible fruit and nuts', 'Фрукты и орехи', 12, 30, true, true),
    ('09', 'II', 'Qahva, choy, ziravorlar', 'Coffee, tea, spices', 'Кофе, чай, пряности', 12, 20, false, false),
    ('11', 'II', 'Un va don mahsulotlari', 'Milling products, malt, starches', 'Мука, солод, крахмал', 12, 25, true, false),
    ('12', 'II', 'Yog''li urug''lar va donlar', 'Oil seeds and oleaginous fruits', 'Масличные семена и плоды', 12, 25, true, false),
    ('13', 'II', 'Shelfak, saqich, smolalar', 'Lac, gums, resins, vegetable saps', 'Шеллак, камеди, смолы', 12, 20, false, false),
    ('14', 'II', 'O''simlik to''qish materiallari', 'Vegetable plaiting materials', 'Растительные материалы для плетения', 12, 25, true, false),
    -- Section III - Animal or Vegetable Fats
    ('16', 'III', 'Go''sht va baliq mahsulotlari', 'Preparations of meat, fish', 'Продукты из мяса и рыбы', 12, 25, true, false),
    -- Section IV - Prepared Foodstuffs
    ('18', 'IV', 'Kakao va kakao mahsulotlari', 'Cocoa and cocoa preparations', 'Какао и продукты из него', 12, 20, false, false),
    ('19', 'IV', 'Don, un, sut mahsulotlari', 'Preparations of cereals, flour, milk', 'Продукты из зерна, муки, молока', 12, 25, true, false),
    ('20', 'IV', 'Sabzavot va meva konservalari', 'Preparations of vegetables, fruit', 'Консервированные овощи и фрукты', 12, 25, true, false),
    ('21', 'IV', 'Turli oziq-ovqat mahsulotlari', 'Miscellaneous edible preparations', 'Прочие пищевые продукты', 12, 20, true, false),
    ('23', 'IV', 'Ozuqa va yem-xashak', 'Residues from food industries, animal feed', 'Корма для животных', 12, 25, true, false),
    -- Section V - Mineral Products
    ('26', 'V', 'Rudalar, shlak, kukun', 'Ores, slag and ash', 'Руды, шлак и зола', 12, 18, true, true),
    -- Section VI - Chemical Products (expanding)
    ('35', 'VI', 'Albumin, kley, fermentlar', 'Albuminoidal substances, glues, enzymes', 'Альбумин, клей, ферменты', 12, 20, false, false),
    ('36', 'VI', 'Porox va portlovchi moddalar', 'Explosives, pyrotechnics', 'Порох и взрывчатые вещества', 12, 18, false, false),
    ('37', 'VI', 'Foto va kino mahsulotlari', 'Photographic goods', 'Фототовары', 12, 15, false, false),
    -- Section VIII - Raw Hides, Skins, Leather
    ('41', 'VIII', 'Teri va xom teri', 'Raw hides and skins, leather', 'Кожа и сырье', 12, 20, true, true),
    ('42', 'VIII', 'Teri buyumlari', 'Articles of leather', 'Изделия из кожи', 12, 20, true, false),
    ('43', 'VIII', 'Mo''yna va sun''iy mo''yna', 'Furfurskins and artificial fur', 'Мех и искусственный мех', 12, 20, false, false),
    -- Section IX - Wood and Articles of Wood
    ('45', 'IX', 'Po''kak va po''kak mahsulotlari', 'Cork and articles of cork', 'Пробка и изделия из нее', 12, 22, false, false),
    ('46', 'IX', 'Somon va to''qima mahsulotlari', 'Manufactures of straw, basketware', 'Изделия из соломы и корзины', 12, 22, true, false),
    -- Section X - Pulp of Wood, Paper
    ('47', 'X', 'Qog''oz massasi', 'Pulp of wood, waste paper', 'Бумажная масса', 12, 20, false, false),
    ('49', 'X', 'Kitob va bosma mahsulotlar', 'Printed books, newspapers', 'Печатные книги, газеты', 12, 15, false, false),
    -- Section XI - Textiles (expanding)
    ('50', 'XI', 'Ipak', 'Silk', 'Шелк', 12, 18, false, false),
    ('51', 'XI', 'Jun', 'Wool, fine animal hair', 'Шерсть', 12, 18, true, false),
    ('53', 'XI', 'O''simlik to''qima tolalari', 'Vegetable textile fibres', 'Растительные текстильные волокна', 12, 18, true, false),
    ('56', 'XI', 'Vatka, namat, arqon', 'Wadding, felt, twine, rope', 'Вата, войлок, веревки', 12, 18, true, false),
    ('57', 'XI', 'Gilam va pol qoplamalari', 'Carpets and floor coverings', 'Ковры и напольные покрытия', 12, 18, true, true),
    ('58', 'XI', 'Maxsus matolar', 'Special woven fabrics', 'Специальные ткани', 12, 18, true, false),
    ('59', 'XI', 'Emdirilgan matolar', 'Impregnated coated fabrics', 'Пропитанные ткани', 12, 18, false, false),
    ('63', 'XI', 'Tayyor to''qimachilik buyumlari', 'Made-up textile articles', 'Прочие текстильные изделия', 12, 20, true, false),
    -- Section XII - Footwear, Headgear
    ('64', 'XII', 'Oyoq kiyimlari', 'Footwear, gaiters', 'Обувь', 12, 20, true, false),
    ('65', 'XII', 'Bosh kiyimlari', 'Headgear and parts', 'Головные уборы', 12, 20, true, false),
    ('66', 'XII', 'Soyabon va hoyalar', 'Umbrellas, walking sticks', 'Зонты, трости', 12, 20, false, false),
    ('67', 'XII', 'Tayyor pat va tuklar', 'Prepared feathers, artificial flowers', 'Перья, искусственные цветы', 12, 20, false, false),
    -- Section XIII - Stone, Plaster, Glass
    ('68', 'XIII', 'Tosh, gips, sement', 'Stone, plaster, cement, asbestos', 'Камень, гипс, цемент', 12, 22, true, false),
    ('71', 'XIII', 'Qimmatbaho metallar va toshlar', 'Precious stones, metals, pearls', 'Драгоценные камни, металлы', 12, 10, true, true),
    -- Section XIV - Pearl, Precious Stones
    -- (covered in 71)
    -- Section XV - Base Metals (expanding)
    ('75', 'XV', 'Nikel va nikel buyumlari', 'Nickel and articles thereof', 'Никель и изделия из него', 12, 18, false, false),
    ('78', 'XV', 'Qo''rg''oshin va undan buyumlar', 'Lead and articles thereof', 'Свинец и изделия из него', 12, 18, true, false),
    ('79', 'XV', 'Rux va rux buyumlari', 'Zinc and articles thereof', 'Цинк и изделия из него', 12, 18, false, false),
    ('80', 'XV', 'Qalay va qalay buyumlari', 'Tin and articles thereof', 'Олово и изделия из него', 12, 18, false, false),
    ('81', 'XV', 'Boshqa asosiy metallar', 'Other base metals, cermets', 'Прочие недрагоценные металлы', 12, 18, false, false),
    ('82', 'XV', 'Asboblar, pichoqlar', 'Tools, cutlery of base metal', 'Инструменты, ножи', 12, 18, true, false),
    ('83', 'XV', 'Turli metall buyumlar', 'Miscellaneous articles of base metal', 'Прочие изделия из металла', 12, 18, true, false),
    -- Section XVI - Machinery (expanding)
    -- (84 and 85 covered in V50)
    -- Section XVII - Vehicles (expanding)  
    ('89', 'XVII', 'Kemalar va suzuvchi vositalar', 'Ships, boats, floating structures', 'Суда и плавсредства', 12, 12, false, false),
    -- Section XVIII - Precision Instruments (expanding)
    ('91', 'XVIII', 'Soatlar', 'Clocks and watches', 'Часы', 12, 15, false, false),
    ('92', 'XVIII', 'Musiqa asboblari', 'Musical instruments', 'Музыкальные инструменты', 12, 15, false, false),
    -- Section XIX - Arms and Ammunition
    ('93', 'XIX', 'Qurol va o''q-dorilar', 'Arms and ammunition', 'Оружие и боеприпасы', 20, 12, false, false),
    -- Section XX - Miscellaneous (expanding)
    ('96', 'XX', 'Turli xil mahsulotlar', 'Miscellaneous manufactured articles', 'Разные товары', 12, 18, true, false),
    -- Section XXI - Works of Art
    ('97', 'XXI', 'San''at asarlari', 'Works of art, antiques', 'Произведения искусства', 12, 10, false, false),
    ('98', 'XXI', 'Maxsus import kodlari', 'Special import codes', 'Специальные импортные коды', 12, 12, false, false)
) AS data
WHERE NOT EXISTS (SELECT 1 FROM hs_code_reference WHERE hs_chapter = data.column1);
