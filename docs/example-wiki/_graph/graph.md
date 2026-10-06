# Wiki graph (fallback view)

```mermaid
graph LR
  index["Index"]
  methods_how_he_builds["How he builds"]
  methods_how_he_debugs["How he debugs"]
  methods_how_he_explains["How he explains"]
  methods_how_he_teaches["How he teaches"]
  methods_how_he_uses_llms["How he uses LLMs"]
  people_eureka_labs["Eureka Labs"]
  principles_complexity_is_the_enemy["Complexity is the enemy"]
  principles_wiki_over_rag["Compile knowledge, don't re-derive it"]
  rules_build_it_or_you_dont_understand_it["Build it or you don't understand it"]
  rules_first_order_term_first["First-order term first"]
  rules_predict_then_run_then_compare["Predict, then run, then compare"]
  rules_prove_it_dont_claim_it["Prove it, don't claim it"]
  rules_say_what_you_assumed["Say what you assumed"]
  rules_show_the_wrong_version_first["Show the wrong version first"]
  rules_simpler_wins["Simpler wins"]
  sources_2017_11_software_2_0["Software 2.0"]
  sources_2019_11_a_recipe_for_training_neural_networks["A Recipe for Training Neural Networks"]
  sources_2023_01_lets_build_gpt_from_scratch["Let's build GPT from scratch"]
  sources_2024_02_lets_build_the_gpt_tokenizer["Let's build the GPT Tokenizer"]
  sources_2025_02_deep_dive_into_llms["Deep Dive into LLMs like ChatGPT"]
  sources_2026_posts_karpathy["X posts (2026)"]
  sources_github_micrograd["micrograd README"]
  sources_github_nanogpt["nanoGPT README"]
  topics_nanogpt_lineage["nanoGPT lineage"]
  topics_tokenization["Tokenization"]
  topics_training_dynamics["Training dynamics"]
  topics_transformers["Transformers"]
  index --> rules_build_it_or_you_dont_understand_it
  index --> rules_first_order_term_first
  index --> rules_predict_then_run_then_compare
  index --> rules_show_the_wrong_version_first
  index --> rules_prove_it_dont_claim_it
  index --> rules_say_what_you_assumed
  index --> rules_simpler_wins
  index --> methods_how_he_explains
  index --> methods_how_he_debugs
  index --> methods_how_he_builds
  index --> methods_how_he_teaches
  index --> methods_how_he_uses_llms
  index --> topics_tokenization
  index --> topics_transformers
  index --> topics_training_dynamics
  index --> topics_nanogpt_lineage
  index --> principles_complexity_is_the_enemy
  index --> principles_wiki_over_rag
  index --> people_eureka_labs
  index --> sources_2024_02_lets_build_the_gpt_tokenizer
  index --> sources_2023_01_lets_build_gpt_from_scratch
  index --> sources_2025_02_deep_dive_into_llms
  index --> sources_2019_11_a_recipe_for_training_neural_networks
  index --> sources_2017_11_software_2_0
  index --> sources_2026_posts_karpathy
  index --> sources_github_nanogpt
  index --> sources_github_micrograd
  methods_how_he_builds --> rules_build_it_or_you_dont_understand_it
  methods_how_he_builds --> topics_nanogpt_lineage
  methods_how_he_debugs --> rules_predict_then_run_then_compare
  methods_how_he_debugs --> rules_prove_it_dont_claim_it
  methods_how_he_debugs --> topics_training_dynamics
  methods_how_he_explains --> rules_first_order_term_first
  methods_how_he_explains --> topics_transformers
  methods_how_he_teaches --> rules_show_the_wrong_version_first
  methods_how_he_teaches --> sources_2025_02_deep_dive_into_llms
  methods_how_he_uses_llms --> rules_say_what_you_assumed
  methods_how_he_uses_llms --> principles_wiki_over_rag
  methods_how_he_uses_llms --> sources_2026_posts_karpathy
  people_eureka_labs --> sources_2025_02_deep_dive_into_llms
  principles_complexity_is_the_enemy --> sources_2017_11_software_2_0
  principles_wiki_over_rag --> sources_2026_posts_karpathy
  principles_wiki_over_rag --> methods_how_he_uses_llms
  rules_build_it_or_you_dont_understand_it --> sources_github_micrograd
  rules_build_it_or_you_dont_understand_it --> sources_2023_01_lets_build_gpt_from_scratch
  rules_build_it_or_you_dont_understand_it --> methods_how_he_teaches
  rules_first_order_term_first --> sources_2023_01_lets_build_gpt_from_scratch
  rules_first_order_term_first --> sources_github_nanogpt
  rules_first_order_term_first --> methods_how_he_explains
  rules_predict_then_run_then_compare --> sources_2024_02_lets_build_the_gpt_tokenizer
  rules_predict_then_run_then_compare --> sources_2019_11_a_recipe_for_training_neural_networks
  rules_predict_then_run_then_compare --> methods_how_he_debugs
  rules_prove_it_dont_claim_it --> sources_2019_11_a_recipe_for_training_neural_networks
  rules_prove_it_dont_claim_it --> sources_2026_posts_karpathy
  rules_prove_it_dont_claim_it --> methods_how_he_debugs
  rules_say_what_you_assumed --> sources_2026_posts_karpathy
  rules_say_what_you_assumed --> methods_how_he_uses_llms
  rules_show_the_wrong_version_first --> sources_2024_02_lets_build_the_gpt_tokenizer
  rules_show_the_wrong_version_first --> methods_how_he_teaches
  rules_simpler_wins --> sources_github_micrograd
  rules_simpler_wins --> sources_2017_11_software_2_0
  rules_simpler_wins --> principles_complexity_is_the_enemy
  sources_2017_11_software_2_0 --> topics_transformers
  sources_2019_11_a_recipe_for_training_neural_networks --> topics_transformers
  sources_2023_01_lets_build_gpt_from_scratch --> topics_transformers
  sources_2024_02_lets_build_the_gpt_tokenizer --> topics_tokenization
  sources_2025_02_deep_dive_into_llms --> topics_transformers
  sources_2026_posts_karpathy --> topics_transformers
  sources_github_micrograd --> topics_transformers
  sources_github_nanogpt --> topics_transformers
  topics_nanogpt_lineage --> sources_github_nanogpt
  topics_nanogpt_lineage --> sources_github_micrograd
  topics_nanogpt_lineage --> people_eureka_labs
  topics_tokenization --> sources_2024_02_lets_build_the_gpt_tokenizer
  topics_tokenization --> topics_transformers
  topics_training_dynamics --> sources_2019_11_a_recipe_for_training_neural_networks
  topics_transformers --> sources_2023_01_lets_build_gpt_from_scratch
  topics_transformers --> topics_nanogpt_lineage
```

- pages: 28 · links: 78
- hubs: topics/transformers, sources/2026-posts-karpathy, sources/2019-11-a-recipe-for-training-neural-networks, sources/2023-01-lets-build-gpt-from-scratch, sources/2024-02-lets-build-the-gpt-tokenizer
- orphans: —
- weak rules (<2 source links): rules/say-what-you-assumed, rules/show-the-wrong-version-first