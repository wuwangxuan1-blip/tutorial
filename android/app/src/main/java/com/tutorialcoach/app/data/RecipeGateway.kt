package com.tutorialcoach.app.data

import com.tutorialcoach.app.domain.DomainAdjustment
import com.tutorialcoach.app.domain.DomainRecipe
import com.tutorialcoach.app.domain.DomainRecipeCompare
import com.tutorialcoach.app.domain.DomainRecipeVersion
import com.tutorialcoach.app.domain.DomainTasting

interface RecipeGateway {
    suspend fun createRecipe(sessionId: String, basePlanVersion: Int, demo: Boolean = false): DomainRecipe

    suspend fun listRecipes(sessionId: String): List<DomainRecipe>

    suspend fun getRecipe(recipeId: String): DomainRecipe

    suspend fun addTasting(recipeId: String, request: TastingRequestDto): DomainTasting

    suspend fun adjustRecipe(
        recipeId: String,
        request: AdjustmentRequestDto,
    ): Pair<DomainRecipe, DomainAdjustment>

    suspend fun listRecipeHistory(recipeId: String): List<DomainRecipeVersion>

    suspend fun compareRecipes(recipeId: String, againstId: String): DomainRecipeCompare
}