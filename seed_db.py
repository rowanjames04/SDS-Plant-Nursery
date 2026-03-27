from app import app, db
from models import Category, Plant, Species, User, Variety


CATEGORY_SEEDS = [
    {
        "name": "Indoor Plants",
        "description": "Low-maintenance greenery for bright rooms, offices, and living spaces.",
        "image_filename": "categories/indoor-plants.jpg",
    },
    {
        "name": "Flowering Plants",
        "description": "Colourful bloomers that add seasonal interest indoors or outdoors.",
        "image_filename": "categories/flowering-plants.jpg",
    },
    {
        "name": "Succulents",
        "description": "Water-wise plants that store moisture and suit sunny spots.",
        "image_filename": "categories/succulents.jpg",
    },
    {
        "name": "Herbs",
        "description": "Edible plants for kitchen gardens, pots, and sunny windowsills.",
        "image_filename": "categories/herbs.jpg",
    },
    {
        "name": "Trees",
        "description": "Feature plants for courtyards, landscapes, and larger garden beds.",
        "image_filename": "categories/trees.jpg",
    },
    {
        "name": "Ferns",
        "description": "Lush foliage plants that prefer filtered light and humidity.",
        "image_filename": "categories/ferns.jpg",
    },
]

SPECIES_SEEDS = [
    {"name": "Monstera deliciosa", "description": "Bold split-leaf foliage with a tropical look."},
    {"name": "Lavandula angustifolia", "description": "Classic lavender known for fragrance and purple flower spikes."},
    {"name": "Aloe vera", "description": "Succulent species with fleshy leaves and easy care."},
    {"name": "Ocimum basilicum", "description": "Sweet basil commonly used in cooking and herb gardens."},
    {"name": "Ficus lyrata", "description": "Architectural fiddle-leaf fig with large glossy leaves."},
    {"name": "Adiantum raddianum", "description": "Delicate maidenhair fern with fine, fan-shaped fronds."},
    {"name": "Salvia rosmarinus", "description": "Hardy rosemary with aromatic needle-like foliage."},
    {"name": "Plumeria rubra", "description": "Tropical flowering tree with a strong fragrance."},
    {"name": "Nephrolepis exaltata", "description": "Classic Boston fern with arching, feathery fronds."},
]

VARIETY_SEEDS = [
    {"name": "Compact", "description": "Smaller growth habit for pots and tighter spaces."},
    {"name": "Variegated", "description": "Distinctive leaf patterning with cream or pale-green markings."},
    {"name": "Fragrant", "description": "Selected for noticeable scent and garden appeal."},
    {"name": "Trailing", "description": "Naturally cascading habit that works well in hanging baskets."},
    {"name": "Dwarf", "description": "A reduced-size form that stays neat and manageable."},
    {"name": "Large Form", "description": "A fuller, larger-growing selection for statement planting."},
]

USER_SEEDS = [
    {
        "email": "staff@sproutsoil.com",
        "full_name": "Nursery Staff",
        "password": "staff123",
        "is_staff": True,
    },
    {
        "email": "customer@example.com",
        "full_name": "Alex Green",
        "password": "password123",
        "is_staff": False,
    },
    {
        "email": "buyer@example.com",
        "full_name": "Jamie Bloom",
        "password": "password123",
        "is_staff": False,
    },
]

PLANT_SEEDS = [
    {
        "common_name": "Swiss Cheese Plant",
        "scientific_name": "Monstera deliciosa",
        "size": 140,
        "category": "Indoor Plants",
        "species": "Monstera deliciosa",
        "variety": "Large Form",
        "pot_container": "230mm nursery pot",
        "price": 39.95,
        "description": "A statement foliage plant with bold split leaves.",
        "colour": "Deep green",
        "growth_width": 120.0,
        "growth_height": 180.0,
        "fragrant": False,
        "frost_sensitive": True,
        "flowering_period": "Rarely flowers indoors",
        "light_requirements": "Bright, indirect light",
        "soil_requirements": "Free-draining indoor potting mix",
        "planting_advice": "Repot when roots start circling the base.",
        "watering_needs": "Water when the top layer of mix dries out.",
        "pruning_needs": "Trim leggy stems to encourage fuller growth.",
        "image_filename": "plants/swiss-cheese-plant.jpg",
    },
    {
        "common_name": "English Lavender",
        "scientific_name": "Lavandula angustifolia",
        "size": 90,
        "category": "Flowering Plants",
        "species": "Lavandula angustifolia",
        "variety": "Fragrant",
        "pot_container": "180mm nursery pot",
        "price": 18.50,
        "description": "Compact lavender with aromatic foliage and purple blooms.",
        "colour": "Purple",
        "growth_width": 80.0,
        "growth_height": 70.0,
        "fragrant": True,
        "frost_sensitive": False,
        "flowering_period": "Spring to summer",
        "light_requirements": "Full sun",
        "soil_requirements": "Well-drained sandy mix",
        "planting_advice": "Plant in a sunny position with excellent drainage.",
        "watering_needs": "Allow soil to dry slightly between waterings.",
        "pruning_needs": "Lightly trim after flowering to keep shape tidy.",
        "image_filename": "plants/english-lavender.jpg",
    },
    {
        "common_name": "Aloe Vera",
        "scientific_name": "Aloe vera",
        "size": 45,
        "category": "Succulents",
        "species": "Aloe vera",
        "variety": "Compact",
        "pot_container": "140mm nursery pot",
        "price": 16.00,
        "description": "Easy-care succulent with thick, soothing leaves.",
        "colour": "Blue-green",
        "growth_width": 50.0,
        "growth_height": 60.0,
        "fragrant": False,
        "frost_sensitive": True,
        "flowering_period": "Occasional summer spikes",
        "light_requirements": "Bright light to full sun",
        "soil_requirements": "Cactus and succulent mix",
        "planting_advice": "Use a pot with excellent drainage holes.",
        "watering_needs": "Water sparingly and let mix dry out fully.",
        "pruning_needs": "Remove damaged outer leaves as needed.",
        "image_filename": "plants/aloe-vera.jpg",
    },
    {
        "common_name": "Sweet Basil",
        "scientific_name": "Ocimum basilicum",
        "size": 25,
        "category": "Herbs",
        "species": "Ocimum basilicum",
        "variety": "Trailing",
        "pot_container": "120mm herb pot",
        "price": 8.95,
        "description": "Fresh culinary herb for pasta, salads, and pesto.",
        "colour": "Lush green",
        "growth_width": 30.0,
        "growth_height": 35.0,
        "fragrant": True,
        "frost_sensitive": True,
        "flowering_period": "Summer",
        "light_requirements": "Full sun to partial shade",
        "soil_requirements": "Rich, free-draining potting mix",
        "planting_advice": "Pinch tips regularly to promote bushy growth.",
        "watering_needs": "Keep evenly moist but not waterlogged.",
        "pruning_needs": "Harvest frequently to prevent flowering.",
        "image_filename": "plants/sweet-basil.jpg",
    },
    {
        "common_name": "Fiddle Leaf Fig",
        "scientific_name": "Ficus lyrata",
        "size": 160,
        "category": "Indoor Plants",
        "species": "Ficus lyrata",
        "variety": "Large Form",
        "pot_container": "250mm nursery pot",
        "price": 59.00,
        "description": "Tall indoor tree with oversized glossy leaves.",
        "colour": "Dark green",
        "growth_width": 100.0,
        "growth_height": 250.0,
        "fragrant": False,
        "frost_sensitive": True,
        "flowering_period": "Not commonly grown for flowers",
        "light_requirements": "Bright indirect light",
        "soil_requirements": "Well-drained indoor mix",
        "planting_advice": "Rotate the pot every few weeks for even growth.",
        "watering_needs": "Water when the top few centimetres feel dry.",
        "pruning_needs": "Remove damaged leaves and lightly shape in spring.",
        "image_filename": "plants/fiddle-leaf-fig.jpg",
    },
    {
        "common_name": "Maidenhair Fern",
        "scientific_name": "Adiantum raddianum",
        "size": 35,
        "category": "Ferns",
        "species": "Adiantum raddianum",
        "variety": "Compact",
        "pot_container": "140mm nursery pot",
        "price": 21.75,
        "description": "Fine-textured fern that prefers humidity and gentle light.",
        "colour": "Fresh green",
        "growth_width": 45.0,
        "growth_height": 40.0,
        "fragrant": False,
        "frost_sensitive": True,
        "flowering_period": "Non-flowering fern",
        "light_requirements": "Filtered light",
        "soil_requirements": "Moist, humus-rich mix",
        "planting_advice": "Keep away from hot, dry air and strong sun.",
        "watering_needs": "Maintain consistent moisture without soggy soil.",
        "pruning_needs": "Remove old fronds at the base as they fade.",
        "image_filename": "plants/maidenhair-fern.jpg",
    },
    {
        "common_name": "Rosemary",
        "scientific_name": "Salvia rosmarinus",
        "size": 55,
        "category": "Herbs",
        "species": "Salvia rosmarinus",
        "variety": "Dwarf",
        "pot_container": "140mm herb pot",
        "price": 11.95,
        "description": "Hardy kitchen herb with a strong aroma and needle-like leaves.",
        "colour": "Grey-green",
        "growth_width": 60.0,
        "growth_height": 70.0,
        "fragrant": True,
        "frost_sensitive": False,
        "flowering_period": "Late winter to spring",
        "light_requirements": "Full sun",
        "soil_requirements": "Sandy, well-drained soil",
        "planting_advice": "Use a raised bed or pot to avoid wet roots.",
        "watering_needs": "Water deeply but infrequently.",
        "pruning_needs": "Trim lightly after flowering to maintain shape.",
        "image_filename": "plants/rosemary.jpg",
    },
    {
        "common_name": "Frangipani",
        "scientific_name": "Plumeria rubra",
        "size": 180,
        "category": "Trees",
        "species": "Plumeria rubra",
        "variety": "Fragrant",
        "pot_container": "300mm nursery pot",
        "price": 74.00,
        "description": "Tropical feature plant with scented summer flowers.",
        "colour": "Pink and yellow",
        "growth_width": 150.0,
        "growth_height": 300.0,
        "fragrant": True,
        "frost_sensitive": True,
        "flowering_period": "Summer to autumn",
        "light_requirements": "Full sun",
        "soil_requirements": "Very free-draining soil",
        "planting_advice": "Protect from frost and keep in a sunny position.",
        "watering_needs": "Water moderately during active growth.",
        "pruning_needs": "Prune in late winter to control height.",
        "image_filename": "plants/frangipani.jpg",
    },
    {
        "common_name": "Boston Fern",
        "scientific_name": "Nephrolepis exaltata",
        "size": 50,
        "category": "Ferns",
        "species": "Nephrolepis exaltata",
        "variety": "Trailing",
        "pot_container": "180mm hanging basket",
        "price": 24.95,
        "description": "Classic trailing fern with arching, feathery fronds.",
        "colour": "Bright green",
        "growth_width": 70.0,
        "growth_height": 55.0,
        "fragrant": False,
        "frost_sensitive": True,
        "flowering_period": "Non-flowering fern",
        "light_requirements": "Filtered light",
        "soil_requirements": "Moist, rich potting mix",
        "planting_advice": "Best suited to sheltered patios or humid interiors.",
        "watering_needs": "Keep evenly moist and mist in dry weather.",
        "pruning_needs": "Cut back tired fronds to encourage fresh growth.",
        "image_filename": "plants/boston-fern.jpg",
    },
]


def get_or_create(model, lookup, defaults=None):
    instance = model.query.filter_by(**lookup).one_or_none()
    if instance is not None:
        return instance, False
    params = dict(lookup)
    if defaults:
        params.update(defaults)
    instance = model(**params)
    db.session.add(instance)
    return instance, True


def seed():
    with app.app_context():
        db.create_all()

        categories = {}
        for seed in CATEGORY_SEEDS:
            category, _ = get_or_create(
                Category,
                {"name": seed["name"]},
                {"description": seed["description"], "image_filename": seed["image_filename"]},
            )
            categories[seed["name"]] = category

        species = {}
        for seed in SPECIES_SEEDS:
            item, _ = get_or_create(
                Species,
                {"name": seed["name"]},
                {"description": seed["description"]},
            )
            species[seed["name"]] = item

        varieties = {}
        for seed in VARIETY_SEEDS:
            item, _ = get_or_create(
                Variety,
                {"name": seed["name"]},
                {"description": seed["description"]},
            )
            varieties[seed["name"]] = item

        for seed in USER_SEEDS:
            get_or_create(
                User,
                {"email": seed["email"]},
                {
                    "full_name": seed["full_name"],
                    "password": seed["password"],
                    "is_staff": seed["is_staff"],
                },
            )

        db.session.flush()

        for seed in PLANT_SEEDS:
            lookup = {"common_name": seed["common_name"]}
            defaults = {
                "image_filename": seed["image_filename"],
                "scientific_name": seed["scientific_name"],
                "size": seed["size"],
                "category_id": categories[seed["category"]].id,
                "species_id": species[seed["species"]].id,
                "variety_id": varieties[seed["variety"]].id,
                "pot_container": seed["pot_container"],
                "price": seed["price"],
                "description": seed["description"],
                "colour": seed["colour"],
                "growth_width": seed["growth_width"],
                "growth_height": seed["growth_height"],
                "fragrant": seed["fragrant"],
                "frost_sensitive": seed["frost_sensitive"],
                "flowering_period": seed["flowering_period"],
                "light_requirements": seed["light_requirements"],
                "soil_requirements": seed["soil_requirements"],
                "planting_advice": seed["planting_advice"],
                "watering_needs": seed["watering_needs"],
                "pruning_needs": seed["pruning_needs"],
            }
            get_or_create(Plant, lookup, defaults)

        db.session.commit()


if __name__ == "__main__":
    seed()
    print("Seeded nursery.db with sample users, categories, species, varieties, and plants.")
