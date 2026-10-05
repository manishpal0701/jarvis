import unittest
from tools.coding.website_researcher import WebsiteResearcher, CompanyResearchContext, CompanyIdentity

class TestCompanyContentAccuracy(unittest.TestCase):
    def test_company_research_identity(self):
        ctx = WebsiteResearcher.research_company("Tesla")
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.entity, "Tesla")
        self.assertIn(ctx.confidence, ("HIGH", "MEDIUM", "LOW"))
        self.assertIsNotNone(ctx.identity)
        self.assertIsInstance(ctx.identity, CompanyIdentity)

if __name__ == '__main__':
    unittest.main()
