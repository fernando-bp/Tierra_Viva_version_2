package com.example.tierravivamarketplace

import android.content.Intent
import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.Spinner
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat

class RegisterActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_register)

        val btn: Button = findViewById(R.id.next_btn)
        btn.setOnClickListener {
            val intent: Intent = Intent(this,RegisterActivityII::class.java)
            startActivity(intent)
        }

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        val spinnerDoc = findViewById<Spinner>(R.id.spinner_docs)
        val optionDoc = arrayOf("C. Ciudadanía", "C. Extranjería")
        spinnerDoc.adapter = ArrayAdapter<String>(this, android.R.layout.simple_list_item_single_choice, optionDoc)
    }
}