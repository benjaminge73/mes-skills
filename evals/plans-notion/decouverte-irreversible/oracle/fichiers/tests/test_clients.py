    def test_le_fichier_de_production_se_charge(self):
        self.assertEqual(len(clients.charger_clients(DONNEES_PRODUCTION)), 6)
