package com.example.tierravivamarketplace

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat


class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {

        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)



        val btnReg: Button=findViewById(R.id.registerbutton)
        btnReg.setOnClickListener {
            val intent: Intent=Intent(this, RegisterActivity:: class.java)
            startActivity(intent)
        }

        val btnLogin: Button=findViewById(R.id.enterbutton)
        btnLogin.setOnClickListener {
            val intent: Intent=Intent(this, UserLogged:: class.java)
            startActivity(intent)
        }

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }
    }
}